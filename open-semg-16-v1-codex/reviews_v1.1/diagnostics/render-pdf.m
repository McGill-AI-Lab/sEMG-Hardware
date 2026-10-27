#import <Cocoa/Cocoa.h>
#import <PDFKit/PDFKit.h>
int main(int argc,const char **argv) { @autoreleasepool {
 PDFDocument *doc=[[PDFDocument alloc] initWithURL:[NSURL fileURLWithPath:@"reviews_v2/diagnostics/final-schematic.pdf"]];
 NSImage *im=[[doc pageAtIndex:0] thumbnailOfSize:NSMakeSize(4200,3000) forBox:kPDFDisplayBoxMediaBox];
 NSBitmapImageRep *rep=[NSBitmapImageRep imageRepWithData:[im TIFFRepresentation]];
 CGImageRef full=[rep CGImage]; CGFloat sx=CGImageGetWidth(full)/594.0,sy=CGImageGetHeight(full)/420.0;
 NSArray *names=@[@"power-view",@"controls-view",@"probes-view",@"reference-view"];
 double box[4][4]={{145,75,70,35},{165,252,95,48},{470,166,120,105},{78,159,88,65}};
 for(int i=0;i<4;i++){
 CGImageRef crop=CGImageCreateWithImageInRect(full,CGRectMake(box[i][0]*sx,box[i][1]*sy,box[i][2]*sx,box[i][3]*sy));
 NSBitmapImageRep *cr=[[NSBitmapImageRep alloc] initWithCGImage:crop];
 [[cr representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:[NSString stringWithFormat:@"reviews_v2/diagnostics/%@.png",names[i]] atomically:YES];
 CGImageRelease(crop);
 }
 } return 0;}
