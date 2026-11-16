// Silueta de la persona fotograma a fotograma con Vision (VNGeneratePersonSegmentationRequest).
// Solo macOS: Vision y AVFoundation son de Apple. Lo compila recorte.py con swiftc.
// Uso: recorte <vídeo> [accurate|balanced|fast]  → máscaras gris de 8 bits (ancho×alto) por stdout.
import AVFoundation
import CoreImage
import Vision

let args = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: args[1]))
let track = try await asset.loadTracks(withMediaType: .video).first!
let reader = try AVAssetReader(asset: asset)
let output = AVAssetReaderTrackOutput(track: track, outputSettings: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
reader.add(output)
reader.startReading()

let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = ["fast": .fast, "balanced": .balanced][args.count > 2 ? args[2] : ""] ?? .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
let ctx = CIContext(options: [.workingColorSpace: NSNull()])
let out = FileHandle.standardOutput
var n = 0
while let sb = output.copyNextSampleBuffer(), let pb = CMSampleBufferGetImageBuffer(sb) {
    let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb)
    try VNImageRequestHandler(cvPixelBuffer: pb).perform([req])
    let m = CIImage(cvPixelBuffer: req.results!.first!.pixelBuffer)
    let s = m.transformed(by: CGAffineTransform(scaleX: CGFloat(w) / m.extent.width,
                                                y: CGFloat(h) / m.extent.height))
    var buf = [UInt8](repeating: 0, count: w * h)
    ctx.render(s, toBitmap: &buf, rowBytes: w, bounds: CGRect(x: 0, y: 0, width: w, height: h),
               format: .L8, colorSpace: nil)
    out.write(Data(buf))
    n += 1
    if n % 300 == 0 { FileHandle.standardError.write("recorte: \(n) fotogramas\n".data(using: .utf8)!) }
}
