dit_name := $(shell ddit targetname)

pkg_files := $(shell find pkg -type f)
src_files := $(shell find src -type f)

.PHONY: clean

all: ${dit_name}

# This makefile depends on 'ddit' which can be installed
# with 'pip3 install daml-dit-ddit'

publish: ${dit_name}
	ddit release

${dit_name}: dit-meta.yaml Makefile ${pkg_files} ${src_files} requirements.txt
	ddit build --force --integration

clean:
	ddit clean
	rm -fr ${dit_name} .daml dist *~ pkg/*~
