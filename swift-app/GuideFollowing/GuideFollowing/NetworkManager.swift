import Foundation
import AVFoundation
import CoreVideo
import UIKit
import Combine

// Detected person has 4 main properties: their ID, their coordinates, the detection confidence, and their distance (in meters) from the camera
struct DetectedPerson: Identifiable, Sendable{
    let id: Int
    let x1, y1, x2, y2: CGFloat
    let conf: Float
    let distance: Float?
}

// The response we get back from /detect on the backend
struct DetectResponse: Codable, Sendable{
    let count: Int
    let boxes: [BoxData]
    let img_w: Int
    let img_h: Int
}

// The individual box data from the backend
struct BoxData: Codable, Sendable{
    let id: Int
    let x1, y1, x2, y2: Float
    let conf: Float
}

// Manages sending frames to the backend and receiving the detection results
class NetworkManager: ObservableObject{
    @Published var detectedPeople: [DetectedPerson] = []
    @Published var trackedPersonID: Int? = nil
    @Published var move: Bool = false
    var depthData: AVDepthData? = nil
    @Published var stoppingDistance: Double = 2.0
    @Published var speed: Double = 1.0
    
    // Backend server address
    // Pis IP
    // @Published var baseURL: String = "http://10.111.161.67:8000"
    // In Lab mac IP
    //@Published var baseURL: String = "http://172.30.109.72:8000"
    // Home IP 
    @Published var baseURL: String = "http://192.168.0.104:8000"

    private var isSending = false
    private var isActive = false
    
    func sendFrame(_ pixelBuffer: CVPixelBuffer){
        // If we are already in the process of sending a frame or tracking has stopped ignore this frame
        guard !isSending, isActive else{
            return
        }
        isSending = true
        // Save the depth data for the current frame
        let currentDepthData = depthData
        
        // Convert the pixel buffer to JPEG image
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else{
            isSending = false
            return
        }
        // Rotate the image 90 degrees so works correctly in portrait mode
        let uiImage = UIImage(cgImage: cgImage, scale: 1.0, orientation: .right)
        // Compress the image so we can send/receive the data faster
        guard let jpegData = uiImage.jpegData(compressionQuality: 0.5) else{
            isSending = false
            return
        }
        
        // Create a request for the backend
        guard let url = URL(string: "\(baseURL)/detect") else{
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 5.0
        
        // Create a unique separator for the form data fields
        let boundary = UUID().uuidString
        // Tell the server we're sending form data with multiple fields
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        // Attach the image and all the data that needs to be sent to the backend
        request.httpBody = buildRequest(jpegData: jpegData, boundary: boundary)
        
        // Send the request to the backend and handle the response
        URLSession.shared.dataTask(with: request){ [weak self] data, response, error in
            defer{
                Task{ @MainActor [weak self] in
                    self?.isSending = false
                }
            }
            
            // Check for errors/if we got data back
            if let error = error{
                print("Network error: \(error.localizedDescription)")
                return
            }
            guard let data = data else{
                print("No data received")
                return
            }

            // Process the backends response on the main thread
            Task{ @MainActor [weak self] in
                guard let self = self else{
                    return
                }
                
                // Decode the response from the server into the DetectResponse struct
                guard let decoded = try? JSONDecoder().decode(DetectResponse.self, from: data) else{
                    print("Failed to decode response")
                    return
                }
                
                // If tracking was stopped while waiting for a response ignore the response
                guard self.isActive else{
                    return
                }
                
                // Convert the backend boxes to our detected person formatting
                let people = decoded.boxes.map{ box in
                    // Calculate the center of the bounding box and get the Depth at the center
                    let centerX = (box.x1+box.x2) / 2
                    let centerY = (box.y1+box.y2) / 2
                    let distance = getDepth(at: centerX, y: centerY, currentDepthData: currentDepthData)
                    return DetectedPerson(id: box.id, x1: CGFloat(box.x1), y1: CGFloat(box.y1), x2: CGFloat(box.x2), y2: CGFloat(box.y2), conf: box.conf, distance: distance)
                }
                // Update the UI to draw the boxes
                self.detectedPeople = people
            }
        }.resume()
    }
    
    // Build the request to send to the backend
    private func buildRequest(jpegData: Data, boundary: String) -> Data{
        var body = Data()
        let boundaryPrefix = "--\(boundary)\r\n"
        let isFollowing = trackedPersonID != nil
        
        // Image field for the request
        body.append(boundaryPrefix.data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"frame.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(jpegData)
        body.append("\r\n".data(using: .utf8)!)
        
        // Model field for the request
        body.append(boundaryPrefix.data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"model\"\r\n\r\n".data(using: .utf8)!)
        body.append("\("n")\r\n".data(using: .utf8)!)
        
        // Following field for when we are following someone
        body.append(boundaryPrefix.data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"following\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(isFollowing)\r\n".data(using: .utf8)!)

        // Only send the trackedPersonID if we are ready to move
        if move{
            if let trackedPersonID{
                body.append(boundaryPrefix.data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"guide_uid\"\r\n\r\n".data(using: .utf8)!)
                body.append("\(trackedPersonID)\r\n".data(using: .utf8)!)
            }
        }

        // Send distance(in meters) if we are following someone and have the depth data
        if let trackedPersonID = trackedPersonID{
            if let trackedPerson = detectedPeople.first(where:{$0.id == trackedPersonID}){
                // Send the distance value if they have one
                if let distance = trackedPerson.distance{
                    body.append(boundaryPrefix.data(using: .utf8)!)
                    body.append("Content-Disposition: form-data; name=\"distance\"\r\n\r\n".data(using: .utf8)!)
                    body.append("\(distance)\r\n".data(using: .utf8)!)
                }
            }
        }
                
        // Close the request
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        return body
    }
    
    // Clear all IDs and start fresh
    func resetTracker(){
        guard let url = URL(string: "\(baseURL)/reset-tracker") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        URLSession.shared.dataTask(with: request) { _, _, _ in }.resume()
    }
    
    // Start processing frames
    func startTracking(){
        isActive = true
    }

    // Stop processing frames and clear all boxes from the screen
    func stopTracking(){
        isActive = false
        trackedPersonID = nil
        DispatchQueue.main.async{
            self.detectedPeople = []
        }
    }

    func setTrackedPersonID(_ id: Int?){
        trackedPersonID = id
    }

    // Returns the distance of who we are following in meters
    private func getDepth(at x: Float, y: Float, currentDepthData: AVDepthData?) -> Float?{
        guard let depthData = currentDepthData else{
                return nil
            }
            
        // convert the depth data to float32 formatting
        let convertedDepth = depthData.converting(toDepthDataType: kCVPixelFormatType_DepthFloat32)
        // Get the depth map into portrait mode
        let orientedDepth = convertedDepth.applyingExifOrientation(.right)
        let depthMap = orientedDepth.depthDataMap
            
        let width = CVPixelBufferGetWidth(depthMap)
        let height = CVPixelBufferGetHeight(depthMap)
            
        // get x and y to be the center of the depth map
        let coordX = Int(x * Float(width))
        let coordY = Int(y * Float(height))
            
        // read the depth data at the center of the bounding box
        CVPixelBufferLockBaseAddress(depthMap, .readOnly)
        // Find the correct row
        let row = CVPixelBufferGetBaseAddress(depthMap)! + coordY * CVPixelBufferGetBytesPerRow(depthMap)
        // Grab the value at the correct column/row in the depth map
        let depth = row.assumingMemoryBound(to: Float32.self)[coordX]
        CVPixelBufferUnlockBaseAddress(depthMap, .readOnly)
            
        return depth
    }
}

