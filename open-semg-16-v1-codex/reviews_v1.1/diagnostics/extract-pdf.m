#import <Foundation/Foundation.h>
#import <PDFKit/PDFKit.h>
int main(int argc,const char **argv) { @autoreleasepool {
 [[NSFileManager defaultManager] createDirectoryAtPath:@"reviews_v2/diagnostics/pdf-text" withIntermediateDirectories:YES attributes:nil error:nil];
 for(int a=1;a<argc;a++) {
 NSString *path=[NSString stringWithUTF8String:argv[a]];
 PDFDocument *d=[[PDFDocument alloc] initWithURL:[NSURL fileURLWithPath:path]];
 NSMutableString *text=[NSMutableString string];
 for(NSUInteger i=0;i<[d pageCount];i++) [text appendFormat:@"\n\n===== PDF PAGE %lu =====\n%@",i+1,[[d pageAtIndex:i] string]];
 NSString *out=[NSString stringWithFormat:@"reviews_v2/diagnostics/pdf-text/%@.txt",[[path lastPathComponent] stringByDeletingPathExtension]];
 [text writeToFile:out atomically:YES encoding:NSUTF8StringEncoding error:nil];
 printf("%s: %lu pages\n",[[path lastPathComponent] UTF8String],[d pageCount]);
 }
 } return 0; }
