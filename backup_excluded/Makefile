all: backup_excluded

backup_excluded: backup_excluded.o
	clang -o $@ $^ -isysroot ../iPhoneOS.sdk -arch armv7 -arch arm64 -framework Foundation

%.o: %.m
	clang -c -o $@ $< -isysroot ../iPhoneOS.sdk -arch armv7 -arch arm64

clean:
	rm -f *.o backup_excluded

install:
	scp backup_excluded ios:/usr/local/bin/backup_excluded
	ssh ios ldid -S /usr/local/bin/backup_excluded
