import AVFoundation
import UIKit
import Combine

// Manages the camera session and provides a video feed to SwiftUI
class CameraManager: NSObject, ObservableObject{
    @Published var previewLayer: AVCaptureVideoPreviewLayer?
    @Published var currentPosition: AVCaptureDevice.Position = .back

    // Our camera session components
    private let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "camera.session.queue")
    private var currentCameraInput: AVCaptureDeviceInput?
    private let depthOutput = AVCaptureDepthDataOutput()

    var onFrameCaptured: ((CVPixelBuffer)->Void)?
    var onDepthCaptured: ((AVDepthData)->Void)?

    override init(){
        super.init()
    }

    // Sets up the camera on a background thread so the app will still launch and not have to wait on this
    func setupCamera(position: AVCaptureDevice.Position = .back){
        currentPosition = position
        sessionQueue.async{ [weak self] in
            if let self = self{
                self.configureCaptureSession(position: position)
            }
        }
    }

    // Configures the camera input, output, and the preview layer
    private func configureCaptureSession(position: AVCaptureDevice.Position){
        captureSession.beginConfiguration()
        captureSession.sessionPreset = .high

        // get and add camera input
        if let camera = AVCaptureDevice.default(.builtInLiDARDepthCamera, for: .video, position: position){
            // Try and create the camera input
            do{
                let input = try AVCaptureDeviceInput(device: camera)
                if captureSession.canAddInput(input){
                    captureSession.addInput(input)
                    currentCameraInput = input
                }
            }catch{
                print("Error setting up the camera input: \(error)")
                captureSession.commitConfiguration()
                return
            }
            
            // add depth output to capture the distance
            if captureSession.canAddOutput(depthOutput){
                captureSession.addOutput(depthOutput)
                depthOutput.setDelegate(self, callbackQueue: sessionQueue)
            }

            // Setup the output to receive frames on the background thread
            videoOutput.setSampleBufferDelegate(self, queue: sessionQueue)
            videoOutput.alwaysDiscardsLateVideoFrames = true

            // Add the output to the session
            if captureSession.canAddOutput(videoOutput){
                captureSession.addOutput(videoOutput)
            }

            captureSession.commitConfiguration()

            // Create preview layer on the main thread
            DispatchQueue.main.async{[weak self] in
                if let self = self{
                    let previewLayer = AVCaptureVideoPreviewLayer(session: self.captureSession)
                    previewLayer.videoGravity = .resizeAspectFill
                    self.previewLayer = previewLayer
                }
            }
        }else{
            print("Failed to get camera for: \(position)")
            captureSession.commitConfiguration()
            return
        }
    }

    func startSession(){
        sessionQueue.async{ [weak self] in
            if let self = self{
                self.captureSession.startRunning()
            }
        }
    }

    func stopSession(){
        sessionQueue.async{ [weak self] in
            if let self = self{
                self.captureSession.stopRunning()
            }
        }
    }
}

// Receives video frames from camera
extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate{
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection){
        // Extract the pixel data from frame
        if let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer){
            onFrameCaptured?(pixelBuffer)
        }
    }
}

// Receives depth data from the camera
extension CameraManager: AVCaptureDepthDataOutputDelegate{
    func depthDataOutput(_ output: AVCaptureDepthDataOutput, didOutput depthData: AVDepthData, timestamp: CMTime, connection: AVCaptureConnection){
        onDepthCaptured?(depthData)
    }
}
