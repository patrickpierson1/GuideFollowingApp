import Foundation
import CoreVideo
import UIKit
import Combine

// Detected person has 3 main properties: their ID, their coordinates, and the detection confidence
struct DetectedPerson: Identifiable, Sendable{
    let id: Int
    let x1, y1, x2, y2: CGFloat
    let conf: Float
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
    @Published var selectedModel: String = "n"
    
    // Backend server address (WILL NEED TO CHANGE TO THE PI'S LATER)
    private let baseURL = "http://192.168.0.102:8000"
    private var isSending = false
    private var isActive = false
    
    func sendFrame(_ pixelBuffer: CVPixelBuffer){
        // If we are already in the process of sending a frame or tracking has stopped ignore this frame
        guard !isSending, isActive else{
            return
        }
        isSending = true
        
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
        // Build the actual form body (image + model + following fields)
        request.httpBody = buildRequest(jpegData: jpegData, boundary: boundary)
        
        // Send the request to the backend
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
                    DetectedPerson(id: box.id, x1: CGFloat(box.x1), y1: CGFloat(box.y1), x2: CGFloat(box.x2), y2: CGFloat(box.y2), conf: box.conf)
                }
                // Update the UI to draw the boxes
                self.detectedPeople = people
            }
        }.resume()
    }
    
    // Builds the request body in multipart form format (like a web file upload)
    private func buildRequest(jpegData: Data, boundary: String) -> Data{
        var body = Data()
        let boundaryPrefix = "--\(boundary)\r\n"
        
        // Image field for the request
        body.append(boundaryPrefix.data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"frame.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(jpegData)
        body.append("\r\n".data(using: .utf8)!)
        
        // Model field for the request
        body.append(boundaryPrefix.data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"model\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(selectedModel)\r\n".data(using: .utf8)!)
        
        // Following field for when we are following someone
        body.append(boundaryPrefix.data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"following\"\r\n\r\n".data(using: .utf8)!)
        body.append("false\r\n".data(using: .utf8)!)
        
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
        DispatchQueue.main.async{
            self.detectedPeople = []
        }
    }
}