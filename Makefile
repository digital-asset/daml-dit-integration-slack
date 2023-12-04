dit_name := $(shell ddit targetname)

pkg_files := $(shell find pkg -type f)
src_files := $(shell find src -type f)

.PHONY: all
all: ${dit_name}

# This makefile depends on 'ddit' which can be installed
# with 'pip3 install daml-dit-ddit'

.PHONY: format
format:
	poetry run isort daml_dit_if
	poetry run black daml_dit_if

.PHONY: typecheck
typecheck:
	poetry tun mypy daml_dit_if

.PHONY: publish
publish: ${dit_name}
	ddit release

${dit_name}: dit-meta.yaml Makefile ${pkg_files} ${src_files} requirements.txt
	ddit build --force --integration

.PHONY: clean
clean:
	ddit clean
	rm -fr ${dit_name} .daml dist *~ pkg/*~
