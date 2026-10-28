#import <Cocoa/Cocoa.h>
#import <PDFKit/PDFKit.h>
int main(int argc, const char **argv) { @autoreleasepool {
 PDFDocument *doc = [[PDFDocument alloc] initWithURL:[NSURL fileURLWithPath:@(argv[1])]];
 PDFPage *page = [doc pageAtIndex:atoi(argv[2])];
 NSSize size = [page boundsForBox:kPDFDisplayBoxMediaBox].size;
 size.width *= 3; size.height *= 3;
 NSImage *img = [page thumbnailOfSize:size forBox:kPDFDisplayBoxMediaBox];
 NSBitmapImageRep *rep = [NSBitmapImageRep imageRepWithData:[img TIFFRepresentation]];
 [[rep representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:@(argv[3]) atomically:YES];
 } return 0; }
