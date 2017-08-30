all: dump_log

dump_log: dump_log.o
	clang -o $@ $^ -isysroot iPhoneOS.sdk -arch armv7 -arch arm64

%.o: %.c
	clang -c -o $@ $< -isysroot iPhoneOS.sdk -arch armv7 -arch arm64

clean:
	rm -f *.o dump_log

install:
	scp dump_log ios:/usr/local/bin/dump_log
	ssh ios ldid -S /usr/local/bin/dump_log
