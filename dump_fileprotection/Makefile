all: dump_fileprotection

dump_fileprotection: dump_fileprotection.o
	clang -o $@ $^ -isysroot iPhoneOS.sdk -arch armv7 -arch arm64 -framework Foundation

%.o: %.m
	clang -c -o $@ $< -isysroot iPhoneOS.sdk -arch armv7 -arch arm64

clean:
	rm -f *.o dump_fileprotection

install:
	scp dump_fileprotection ios:/usr/local/bin/dump_fileprotection
	ssh ios ldid -S /usr/local/bin/dump_fileprotection
