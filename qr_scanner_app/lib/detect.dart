import 'package:http/http.dart' as http;
import 'dart:convert';

List<String> suspiciousTlds = [
  ".aaa", ".aarp", ".abarth", ".abb",  ".abbott", ".xyz", ".club", ".top"
];

List<String> suspiciousEncodings = ['%20', '%22', '%3C', '%3E'];

bool isIpAddressInUrl(String url) {
  final ipRegex = RegExp(
      r'((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)');
  return ipRegex.hasMatch(url);
}

bool isUrlTooLong(String url) {
  return url.length > 54;
}

bool containsAtSymbol(String url) {
  return url.contains('@');
}

bool containsDash(String url) {
  return url.contains('-');
}

bool hasTooManyDots(String url) {
  int dotCount = '.'.allMatches(url).length;
  return dotCount >= 4;
}

bool isHttpProtocol(String url) {
  Uri parsedUrl = Uri.parse(url);
  return parsedUrl.scheme == 'http';
}

bool hasTooManySlashes(String url) {
  int slashCount = '/'.allMatches(url).length;
  return slashCount >= 6;
}

String getTld(String url) {
  Uri parsedUrl = Uri.parse(url);
  return parsedUrl.host.split('.').last;
}

bool isSuspiciousTld(String url) {
  String tld = "." + getTld(url);
  return suspiciousTlds.contains(tld);
}

bool containsSuspiciousEncodings(String url) {
  for (var encoding in suspiciousEncodings) {
    if (url.contains(encoding)) {
      return true;
    }
  }
  return false;
}

Future<String> traceRedirects(String url) async {
  try {
    var client = http.Client();
    var request = http.Request('GET', Uri.parse(url));
    request.followRedirects = true;
    request.maxRedirects = 1;

    var response = await client.send(request);
    var finalUri = response.request!.url.toString();
    return finalUri;
  } catch (e) {
    return url;
  }
}

Future<String> logDetectedUrl(String url) async {
  try {
    final response = await http.post(
      Uri.parse('http://10.80.6.238:8000/log_detected_url'),  // FastAPI 서버 URL
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'url': url}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['prediction'] == 1) {
        return "머신러닝으로 탐지됨";
      } else {
        return "정상 사이트";
      }
    } else {
      return "FastAPI 서버 오류: 상태 코드 ${response.statusCode}";
    }
  } catch (e) {
    return "FastAPI 요청 실패: $e";
  }
}

// MongoDB에 URL 확인 요청 추가
Future<String> checkUrl(String url) async {
  try {
    final response = await http.post(
      Uri.parse('http://10.80.6.238:8000/check-url'), // 실제 IP로 변경
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'url': url}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      if (data['isBlacklisted']) {
        return "블랙리스트로 탐지됨"; // 블랙리스트 URL
      }

      if (data['isWhitelisted']) {
        return "화이트리스트로 탐지됨"; // 화이트리스트 URL
      }
    } else {
      return "FastAPI 서버 오류: 상태 코드 ${response.statusCode}";
    }
  } catch (e) {
    return "FastAPI 요청 실패: $e";
  }

  // 기존 로직 실행
  int maliciousCount = 0;

  if (containsSuspiciousEncodings(url)) {
    maliciousCount++;
  }
  if (isIpAddressInUrl(url)) {
    maliciousCount++;
  }
  if (isUrlTooLong(url)) {
    maliciousCount++;
  }
  if (containsAtSymbol(url)) {
    maliciousCount++;
  }
  if (containsDash(url)) {
    maliciousCount++;
  }
  if (hasTooManyDots(url)) {
    maliciousCount++;
  }
  if (isHttpProtocol(url)) {
    maliciousCount++;
  }
  if (hasTooManySlashes(url)) {
    maliciousCount++;
  }

  String finalLandingPage = await traceRedirects(url);
  if (finalLandingPage != url) {
    maliciousCount++;
  }

  if (maliciousCount >= 2) {
    return "피싱 사이트로 탐지됨(스태틱 탐지)"; // 피싱 사이트 탐지
  } else {
    // 피싱으로 탐지되지 않은 경우 FastAPI 서버에 URL 로그 전송
    await logDetectedUrl(url);
    return "정상 사이트"; // 정상 사이트
  }
}
