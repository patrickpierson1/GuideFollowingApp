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

    var onFrameCaptured: ((CVPixelBuffer)->Void)?

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
        if let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: position){
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

    // Switches between the front and back camera
    func switchCamera(){
        // Run on the background thread
        sessionQueue.async{ [weak self] in
            if let self = self{
                self.captureSession.beginConfiguration()

                // Remove the current camera
                if let currentInput = self.currentCameraInput{
                    self.captureSession.removeInput(currentInput)
                }
                
                // Check the current position of the camera and change our new position to the opposite
                let newPosition: AVCaptureDevice.Position
                if self.currentPosition == .back{
                    newPosition = .front
                }else{
                    newPosition = .back
                }
                // Try to get the new camera device
                if let newCamera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: newPosition){
                    do{
                        // Wrap the camera device as input and see if we can add it to the session
                        let newInput = try AVCaptureDeviceInput(device: newCamera)
                        if self.captureSession.canAddInput(newInput){
                            self.captureSession.addInput(newInput)
                            self.currentCameraInput = newInput

                            // Update the position on our main thread
                            DispatchQueue.main.async{
                                self.currentPosition = newPosition
                            }
                        }
                    }catch{
                        print("Error when switching cameras: \(error)")
                        // If we couldnt add the new camera just restore the old camera
                        if let currentInput = self.currentCameraInput{
                            self.captureSession.addInput(currentInput)
                        }
                    }
                }else{
                    print("Failed to get new camera")
                    // If switching cameras fails just stay at the same camera
                    if let currentInput = self.currentCameraInput{
                        self.captureSession.addInput(currentInput)
                    }
                }
                // Apply all the changes we have made
                self.captureSession.commitConfiguration()
            }
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