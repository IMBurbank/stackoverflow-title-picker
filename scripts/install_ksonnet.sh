#!/bin/sh

. $(dirname $0)/dev.env.sh

# Create ~/bin if it doesn't exist
if [ ! -e "${HOME}/bin" ]; then
	# Create `bin` directory in $HOME
	mkdir -p ${HOME}/bin
	export PATH=$PATH:${HOME}/bin/
	echo "export PATH=$PATH:${HOME}/bin/" >> .bashrc
fi

# Remove old ks if it exists in ~/bin
[ -e "${HOME}/bin/ks" ] && rm "${HOME}/bin/ks"

# Download Ksonnet executable into ~/bin/
curl -Lk https://github.com/ksonnet/ksonnet/releases/download/v${KS_VER}/${KS_PKG}.tar.gz \
	| tar xzv -C $HOME/bin/ ${KS_PKG}/ks --strip=1