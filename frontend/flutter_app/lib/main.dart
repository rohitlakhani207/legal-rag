import 'package:flutter/material.dart';

import 'api/api_client.dart';
import 'app.dart';
import 'deep_link.dart';

void main() {
  runApp(LegalRagApp(api: HttpLegalRagApi(), link: DeepLink.fromUri(Uri.base)));
}
