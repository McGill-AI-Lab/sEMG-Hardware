#import <Cocoa/Cocoa.h>
#import <PDFKit/PDFKit.h>
int main(int argc, const char **argv) { @autoreleasepool {
    if (argc != 3) return 2;
    PDFDocument *doc = [[PDFDocument alloc] initWithURL:[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]]];
    if (!doc || doc.pageCount != 1) return 3;
    NSImage *image = [[doc pageAtIndex:0] thumbnailOfSize:NSMakeSize(8400,6000) forBox:kPDFDisplayBoxMediaBox];
    NSBitmapImageRep *rep = [NSBitmapImageRep imageRepWithData:[image TIFFRepresentation]];
    CGImageRef full = rep.CGImage;
    double sx = CGImageGetWidth(full)/594.0, sy = CGImageGetHeight(full)/420.0;
    NSArray *names = @[@"power-view.png",@"mcu-nc-view.png",@"supply-alias-view.png"];
    double boxes[3][4] = {{72,257,105,42},{500,22,88,112},{143,76,90,89}};
    NSString *output = [NSString stringWithUTF8String:argv[2]];
    for (int i=0;i<3;i++) {
        CGImageRef crop=CGImageCreateWithImageInRect(full,CGRectMake(boxes[i][0]*sx,boxes[i][1]*sy,boxes[i][2]*sx,boxes[i][3]*sy));
        NSBitmapImageRep *cr=[[NSBitmapImageRep alloc] initWithCGImage:crop];
        if (![[cr representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:[output stringByAppendingPathComponent:names[i]] atomically:YES]) return 4;
        CGImageRelease(crop);
    }
    return 0;
}}
