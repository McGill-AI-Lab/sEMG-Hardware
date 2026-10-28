#import <Cocoa/Cocoa.h>
#import <PDFKit/PDFKit.h>
int main(int argc,const char **argv) { @autoreleasepool {
    if(argc!=3)return 2;
    PDFDocument *doc=[[PDFDocument alloc]initWithURL:[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]]];
    if(!doc || doc.pageCount!=1)return 3;
    NSImage *im=[[doc pageAtIndex:0]thumbnailOfSize:NSMakeSize(10000,7100) forBox:kPDFDisplayBoxMediaBox];
    NSBitmapImageRep *rep=[NSBitmapImageRep imageRepWithData:[im TIFFRepresentation]];
    CGImageRef full=rep.CGImage;
    double sx=CGImageGetWidth(full)/841.0,sy=CGImageGetHeight(full)/594.0;
    double boxes[4][4]={{15,45,275,220},{15,265,280,190},{610,45,220,350},{15,470,810,65}};
    NSArray *names=@[@"adc-input-view.png",@"adc-bypass-view.png",@"esp-interface-view.png",@"limits-view.png"];
    NSString *out=[NSString stringWithUTF8String:argv[2]];
    for(int n=0;n<4;n++){
        CGImageRef crop=CGImageCreateWithImageInRect(full,CGRectMake(boxes[n][0]*sx,boxes[n][1]*sy,boxes[n][2]*sx,boxes[n][3]*sy));
        NSBitmapImageRep *cr=[[NSBitmapImageRep alloc]initWithCGImage:crop];
        [[cr representationUsingType:NSBitmapImageFileTypePNG properties:@{}]writeToFile:[out stringByAppendingPathComponent:names[n]]atomically:YES];
        CGImageRelease(crop);
    }
    return 0;
}}
