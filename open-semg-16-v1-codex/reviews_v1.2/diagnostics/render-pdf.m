#import <Cocoa/Cocoa.h>
#import <PDFKit/PDFKit.h>
int main(int argc, const char **argv) { @autoreleasepool {
    if (argc != 3) return 2;
    NSString *input = [NSString stringWithUTF8String:argv[1]];
    NSString *output = [NSString stringWithUTF8String:argv[2]];
    PDFDocument *doc = [[PDFDocument alloc] initWithURL:[NSURL fileURLWithPath:input]];
    if (!doc || doc.pageCount != 1) return 3;
    NSImage *image = [[doc pageAtIndex:0] thumbnailOfSize:NSMakeSize(8400,6000) forBox:kPDFDisplayBoxMediaBox];
    NSBitmapImageRep *rep = [NSBitmapImageRep imageRepWithData:[image TIFFRepresentation]];
    CGImageRef full = rep.CGImage;
    double sx = CGImageGetWidth(full)/594.0, sy = CGImageGetHeight(full)/420.0;
    NSArray *names = @[@"new-controls-view.png", @"requirements-view.png"];
    double boxes[2][4] = {{165,295,99,55},{264,260,327,85}};
    for (int i=0;i<2;i++) {
        CGImageRef crop = CGImageCreateWithImageInRect(full,CGRectMake(boxes[i][0]*sx,boxes[i][1]*sy,boxes[i][2]*sx,boxes[i][3]*sy));
        NSBitmapImageRep *cr = [[NSBitmapImageRep alloc] initWithCGImage:crop];
        NSData *png = [cr representationUsingType:NSBitmapImageFileTypePNG properties:@{}];
        if (![png writeToFile:[output stringByAppendingPathComponent:names[i]] atomically:YES]) return 4;
        CGImageRelease(crop);
    }
    return 0;
}}
