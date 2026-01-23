import AVFoundation
import UIKit
import Combine

class CameraManager: NSObject, ObservableObject{
    @Published var previewLayer: AVCaptureVideoPreviewLayer?
    @Published var currentPosition: AVCaptureDevice.Position = .back

    private let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "camera.session.queue")

    private var currentCameraInput: AVCaptureDeviceInput?

    var onFrameCaptured: ((CVPixelBuffer)->Void)?

    override init(){
        super.init()
    }

    func setupCamera(position: AVCaptureDevice.Position = .back){
        currentPosition = position
        sessionQueue.async { [weak self] in
            self?.configureCaptureSession(position: position)
        }
    }

    private func configureCaptureSession(position: AVCaptureDevice.Position){
        captureSession.beginConfiguration()
        captureSession.sessionPreset = .high

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: position)else {
            print("Failed to get camera for: \(position)")
            captureSession.commitConfiguration()
            return
        }

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

        videoOutput.setSampleBufferDelegate(self, queue: sessionQueue)
        videoOutput.alwaysDiscardsLateVideoFrames = true

        if captureSession.canAddOutput(videoOutput){
            captureSession.addOutput(videoOutput)
        }

        captureSession.commitConfiguration()

        DispatchQueue.main.async{[weak self] in
            guard let self = self else{
                return
            }
            let previewLayer = AVCaptureVideoPreviewLayer(session: self.captureSession)
            previewLayer.videoGravity = .resizeAspectFill
            self.previewLayer = previewLayer
        }
    }

    func switchCamera(){
        sessionQueue.async{ [weak self] in
            guard let self = self else{
                return
            }
            self.captureSession.beginConfiguration()

            if let currentInput = self.currentCameraInput{
                self.captureSession.removeInput(currentInput)
            }

            let newPosition: AVCaptureDevice.Position = self.currentPosition == .back ? .front :.back

            guard let newCamera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: newPosition) else{
                print("Failed to get new camera")

                if let currentInput = self.currentCameraInput{
                    self.captureSession.addInput(currentInput)
                }
                self.captureSession.commitConfiguration()
                return
            }

            do{
                let newInput = try AVCaptureDeviceInput(device: newCamera)
                if self.captureSession.canAddInput(newInput){
                    self.captureSession.addInput(newInput)
                    self.currentCameraInput = newInput

                    DispatchQueue.main.async{
                        self.currentPosition = newPosition
                    }
                }
            } catch{
                print("Error when switching cameras: \(error)")
                if let currentInput = self.currentCameraInput{
                    self.captureSession.addInput(currentInput)
                }
            }

            self.captureSession.commitConfiguration()
        }
    }

    func startSession(){
        sessionQueue.async { [weak self] in
            self?.captureSession.startRunning()
        }
    }

    func stopSession(){
        sessionQueue.async { [weak self] in
            self?.captureSession.stopRunning()
        }
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate{
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection){
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else{
            return
        }
        onFrameCaptured?(pixelBuffer)
    }
}
