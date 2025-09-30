/**
 * Script to create test fixture files for E2E tests.
 * Run this before running E2E tests to ensure fixtures exist.
 */

const fs = require('fs');
const path = require('path');

const fixturesDir = __dirname;

// Ensure fixtures directory exists
if (!fs.existsSync(fixturesDir)) {
  fs.mkdirSync(fixturesDir, { recursive: true });
}

// Create test image files (1x1 pixel images with different formats)
const createTestImage = (filename, mimeType = 'image/jpeg') => {
  // Minimal JPEG header for a 1x1 pixel image
  const jpegData = Buffer.from([
    0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
    0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
    0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
    0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
    0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
    0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
    0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
    0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x11, 0x08, 0x00, 0x01,
    0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01,
    0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0xFF, 0xC4,
    0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xDA, 0x00, 0x0C,
    0x03, 0x01, 0x00, 0x02, 0x11, 0x03, 0x11, 0x00, 0x3F, 0x00, 0x80, 0xFF, 0xD9
  ]);

  fs.writeFileSync(path.join(fixturesDir, filename), jpegData);
};

// Create test PDF file
const createTestPDF = (filename) => {
  // Minimal PDF structure
  const pdfData = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000306 00000 n
0000000399 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
522
%%EOF`;

  fs.writeFileSync(path.join(fixturesDir, filename), pdfData);
};

// Create executable file for testing unsupported formats
const createExecutableFile = (filename) => {
  const exeData = Buffer.from([0x4D, 0x5A, 0x90, 0x00]); // DOS header
  fs.writeFileSync(path.join(fixturesDir, filename), exeData);
};

// Create large file for testing file size limits
const createLargeFile = (filename, sizeMB = 15) => {
  const data = Buffer.alloc(sizeMB * 1024 * 1024, 0x41); // Fill with 'A'
  fs.writeFileSync(path.join(fixturesDir, filename), data);
};

console.log('Creating test fixture files...');

// Create various test images
createTestImage('solar-panel-receipt.jpg');
createTestImage('led-lights-receipt.jpg');
createTestImage('water-conservation.jpg');
createTestImage('waste-management.jpg');
createTestImage('mobile-photo.jpg');
createTestImage('high-res-photo.jpg');
createTestImage('corrupt-image.jpg'); // Will be corrupted later

// Create test documents
createTestPDF('energy-bill.pdf');
createTestPDF('large-document.pdf');

// Create unsupported files
createExecutableFile('document.exe');

// Create large file for size testing
createLargeFile('large-image.jpg', 15);

// Corrupt the corrupt image file
const corruptPath = path.join(fixturesDir, 'corrupt-image.jpg');
fs.writeFileSync(corruptPath, Buffer.from([0x00, 0x00, 0x00, 0x00]));

console.log('✅ Test fixture files created successfully!');

// List created files
console.log('\nCreated files:');
fs.readdirSync(fixturesDir).forEach(file => {
  const stats = fs.statSync(path.join(fixturesDir, file));
  console.log(`  ${file} (${Math.round(stats.size / 1024)}KB)`);
});

console.log('\n🎯 Ready to run E2E tests!');