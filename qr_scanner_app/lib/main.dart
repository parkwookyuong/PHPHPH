import 'package:flutter/material.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'package:mobile_scanner/mobile_scanner.dart';  // mobile_scanner 패키지 사용
import 'detect.dart';  // detect.dart 파일을 import
import 'package:camera/camera.dart';  // camera 패키지 import

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      final firstCamera = cameras.first;
      runApp(MaterialApp(
        title: '안심 QR',
        home: MainPage(camera: firstCamera),
      ));
    } else {
      runApp(MaterialApp(
        title: '안심 QR',
        home: ErrorPage(errorMessage: '카메라를 찾을 수 없습니다.'),
      ));
    }
  } catch (e) {
    runApp(MaterialApp(
      title: '안심 QR',
      home: ErrorPage(errorMessage: '카메라 초기화 중 오류가 발생했습니다: $e'),
    ));
  }
}

class ErrorPage extends StatelessWidget {
  final String errorMessage;

  const ErrorPage({Key? key, required this.errorMessage}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text(
          errorMessage,
          style: TextStyle(color: Colors.red, fontSize: 18),
        ),
      ),
    );
  }
}

class MainPage extends StatelessWidget {
  final CameraDescription camera;

  const MainPage({Key? key, required this.camera}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(height: 100),
            Image.asset(
              'assets/images/main_02.png',
              width: 300,
            ),
            SizedBox(height: 80),
            GestureDetector(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => TakePictureScreen(camera: camera),
                  ),
                );
              },
              child: Image.asset(
                'assets/images/start.png',
                width: 250,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class TakePictureScreen extends StatefulWidget {
  final CameraDescription camera;

  const TakePictureScreen({Key? key, required this.camera}) : super(key: key);

  @override
  State<TakePictureScreen> createState() => _TakePictureScreenState();
}

class _TakePictureScreenState extends State<TakePictureScreen> {
  late CameraController _controller;
  late Future<void> _initializeControllerFuture;
  String detectionMessage = "QR 코드 스캔 중...";
  String detectedUrl = "";  // 탐지된 URL을 저장
  String imagePath = "";  // 결과에 따른 이미지 경로
  bool isProcessing = false; // 스캔 플래그 추가

  @override
  void initState() {
    super.initState();
    _controller = CameraController(
      widget.camera,
      ResolutionPreset.high, // Adjusted for better 3:4 aspect ratio
    );
    _initializeControllerFuture = _controller.initialize();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Image.asset(
          'assets/images/main.png',
          height: 40,
        ),
      ),
      backgroundColor: Colors.white,
      body: FutureBuilder<void>(
        future: _initializeControllerFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            return Column(
              children: [
                AspectRatio(
                  aspectRatio: 3 / 4, // Set camera view to 3:4 aspect ratio
                  child: Stack(
                    children: [
                      MobileScanner(
                        onDetect: (BarcodeCapture barcodeCapture) async {
                          if (isProcessing) {
                            // 현재 처리 중이면 이벤트를 무시
                            return;
                          }

                          final List<Barcode> barcodes = barcodeCapture.barcodes;
                          if (barcodes.isNotEmpty) {
                            final String? scannedUrl = barcodes.first.rawValue;

                            if (scannedUrl != null) {
                              setState(() {
                                isProcessing = true; // 스캔 시작
                                // detectionMessage = "피싱 분석 중...";
                                imagePath = "assets/images/preprocessing.png";
                              });

                              try {
                                // 서버 호출 및 결과 가져오기
                                String detectionResult = await checkUrl(scannedUrl);

                                setState(() {
                                  detectedUrl = scannedUrl;

                                  if (detectionResult == "블랙리스트로 탐지됨") {
                                    detectionMessage = "블랙리스트로 탐지됨";
                                    imagePath = 'assets/images/pshing.png';
                                  } else if (detectionResult == "화이트리스트로 탐지됨") {
                                    detectionMessage = "화이트리스트로 탐지됨";
                                    imagePath = 'assets/images/safe.png';
                                  } else if (detectionResult == "피싱 사이트로 탐지됨(스태틱 탐지)") {
                                    detectionMessage = "피싱 사이트로 탐지됨(스태틱 탐지)";
                                    imagePath = 'assets/images/pshing.png';
                                  } else if (detectionResult == "머신러닝으로 탐지됨") {
                                    detectionMessage = "정상 사이트";
                                    imagePath = 'assets/images/safe.png';
                                  } else if (detectionResult == "정상 사이트") {
                                    detectionMessage = "머신러닝으로 탐지됨";
                                    imagePath = 'assets/images/pshing.png';
                                  } else {
                                    detectionMessage = "오류 발생";
                                    imagePath = '';
                                  }
                                });

                                // 10초 대기
                                await Future.delayed(Duration(seconds: 10));
                              } catch (e) {
                                setState(() {
                                  detectionMessage = "오류 발생: $e";
                                  imagePath = '';
                                });
                              } finally {
                                setState(() {
                                  isProcessing = false; // 처리 완료 후 플래그 해제
                                });
                              }
                            }
                          }
                        },
                      ),
                      Positioned.fill(
                        child: Image.asset(
                          'assets/images/scan_02.png',
                          fit: BoxFit.cover,
                        ),
                      ),
                      Positioned.fill(
                        child: CustomPaint(
                          painter: GridPainter(),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  color: Colors.white,
                  padding: EdgeInsets.all(16.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (imagePath.isNotEmpty)
                        Image.asset(imagePath, width: 100),
                      SizedBox(height: 16),
                      Text(
                        detectionMessage,
                        style: TextStyle(color: Colors.black, fontSize: 18),
                      ),
                      if (detectedUrl.isNotEmpty)
                        Text(
                          detectedUrl,
                          style: TextStyle(color: Colors.grey, fontSize: 16),
                        ),
                    ],
                  ),
                ),
              ],
            );
          } else {
            return Center(child: CircularProgressIndicator());
          }
        },
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: GestureDetector(
        onTap: () async {
          try {
            await _initializeControllerFuture;

            final image = await _controller.takePicture();

            final path = join(
              (await getTemporaryDirectory()).path,
              '${DateTime.now()}.png',
            );

            File(image.path).copy(path);

            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => DisplayPictureScreen(imagePath: path),
              ),
            );
          } catch (e) {
            print(e);
          }
        },
        child: Image.asset('assets/images/camera.png', width: 50, height: 50),
      ),
    );
  }
}

class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.5)
      ..strokeWidth = 1;

    for (int i = 1; i < 3; i++) {
      double dy = size.height * i / 3;
      canvas.drawLine(Offset(0, dy), Offset(size.width, dy), paint);
    }

    for (int i = 1; i < 3; i++) {
      double dx = size.width * i / 3;
      canvas.drawLine(Offset(dx, 0), Offset(dx, size.height), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return false;
  }
}

class DisplayPictureScreen extends StatelessWidget {
  final String imagePath;

  const DisplayPictureScreen({Key? key, required this.imagePath}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Captured Image'),
      ),
      body: Image.file(File(imagePath)),
    );
  }
}
