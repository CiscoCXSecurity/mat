#import <Foundation/Foundation.h>
#include <stdio.h>
#include <stdlib.h>

int main (int argc, char **argv) {
    NSError *error = nil;
    id flag = nil;
    if (argc == 2) {
        NSURL *file = [NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]];
        [file getResourceValue: &flag forKey: NSURLIsExcludedFromBackupKey error: &error];
        printf("%d\n", [flag boolValue]);
        exit(EXIT_SUCCESS);
    } else {
        exit(EXIT_FAILURE);
    }
}
