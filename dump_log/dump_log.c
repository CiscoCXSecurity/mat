/* Based on https://projects.nth-dimension.org.uk/projects/ios-application-analyser/repository/show/trunk/src/tools/dump_log */

#include <asl.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include <time.h>

void print_log(aslmsg aslmessage) {
    time_t raw_time = atoi(asl_get(aslmessage, ASL_KEY_TIME));
    const char *message = asl_get(aslmessage, ASL_KEY_MSG);
    if(message != NULL)
        printf("%.24s %s[%s]: %s\n", ctime(&raw_time), asl_get(aslmessage, ASL_KEY_SENDER), asl_get(aslmessage, ASL_KEY_PID), message);
}

void dump_entry(aslmsg aslmessage) {
    printf("------------------------------ Log Message ------------------------------\n");
    const char *keystring;
    int keyindex = 0;
    while ((keystring = asl_key(aslmessage, keyindex++)) != NULL)
        printf("%s: %s\n", keystring, asl_get(aslmessage, keystring));
    printf("------------------------------ End Message ------------------------------\n");
}

int dump_log(int message_id, int dump, char *search){
    aslmsg aslmessage;
    aslresponse aslresponse = asl_search(NULL, asl_new(ASL_TYPE_QUERY));
    int last_message_id;

    while ((aslmessage = asl_next(aslresponse)) != NULL) {
        last_message_id = atoi(asl_get(aslmessage, ASL_KEY_MSG_ID));
        if ( last_message_id > message_id &&
                (
                    search == NULL ||
                    strstr(asl_get(aslmessage, ASL_KEY_SENDER) , search) ||
                    strstr(asl_get(aslmessage, ASL_KEY_PID) , search)
                )
            ) {
            if (dump)
                dump_entry(aslmessage);
            else
                print_log(aslmessage);
        }
    }

    // Cleanup
    asl_release(aslresponse);
    return last_message_id;
}

void print_help(char *name){
    printf("\nusage: %s [-h] [-i] [-d] [PID | APP_NAME]\n", name);
    printf(" -h                  Prints this help information\n");
    printf(" -i                  Non stop printing logs, equivalent of tail -f\n");
    printf(" -d                  Dumps all entries of the log message instead of printing them properly\n");
    printf(" [PID | APP_NAME]    Tries to filter the logs by app name or PID\n\n");
    exit(EXIT_SUCCESS);
}

int main(int argc, char **argv) {
    int secs = 0, dump = 0, non_stop = 0, last_message_id = -1;
    char *search;

    for(secs = 1; secs < argc; secs++)
        if (strstr(argv[secs], "-h"))
            print_help(argv[0]);
        else if (strstr(argv[secs], "-d"))
            dump = 1;
        else if (strstr(argv[secs], "-i"))
            non_stop = 1;
        else search = argv[secs];

    do {
        last_message_id = dump_log(last_message_id, dump, search);
    } while ( non_stop );

    exit(EXIT_SUCCESS);
}
