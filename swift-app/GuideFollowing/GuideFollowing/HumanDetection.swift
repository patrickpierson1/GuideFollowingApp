import Vision
import AVFoundation
import Combine

class HumanDetection: ObservableObject{
    @Published var peopleCount: Int = 0


    // Vision request for detecting people
    private let humanDetectionRequest: VNDetectHumanRectanglesRequest = {
        let request = VNDetectHumanRectanglesRequest()
        // Testing with only the upper body cause detecting full body was causing some problems.
        // (Seems to work better than detecting full body so will probably keep it)
        request.upperBodyOnly = true
        return request
    }()

    // Function that processes a frame to detect people
    func detectPeople(in pixelBuffer: CVPixelBuffer){

        // process the frame
        let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, options: [:])

        do{
            // run the detection
            try handler.perform([humanDetectionRequest])

            // process the results on the main thread
            DispatchQueue.main.async{ [weak self] in
                self?.processResults()
            }
        }catch{
            print("Error: \(error)")
        }
    }

    // Update the count of people
    private func processResults(){
        if let results = humanDetectionRequest.results{
            peopleCount = results.count
        }else{
            peopleCount=0
        }
    }
}
