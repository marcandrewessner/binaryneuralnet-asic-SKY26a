# Bootstrap using librelane's own flake-compat so no separate flake.lock is needed.
let
  librelaneSrc = builtins.fetchGit { url = "https://github.com/librelane/librelane"; };
  lock = builtins.fromJSON (builtins.readFile "${librelaneSrc}/flake.lock");
  flake-compat = fetchTarball {
    url =
      lock.nodes.flake-compat.locked.url
        or "https://github.com/edolstra/flake-compat/archive/${lock.nodes.flake-compat.locked.rev}.tar.gz";
    sha256 = lock.nodes.flake-compat.locked.narHash;
  };
  librelaneFlake = (import flake-compat { src = librelaneSrc; }).defaultNix;
  pkgs = librelaneFlake.legacyPackages.${builtins.currentSystem};
in
pkgs.mkShell {
  inputsFrom = [
    (pkgs.librelane-shell.override {
      extra-packages = with pkgs; [ gnumake bear gcc SDL2 SDL2.dev ];
      extra-python-packages =
        ps: with ps; [
          cocotb
          cocotb-bus
        ];
    })
  ];
  shellHook = ''
    export PDK_ROOT="$(pwd)/.pdk"
    if [ -z "$DISPLAY" ]; then
      echo "WARNING: \$DISPLAY is not set — GUI tools like Magic will fail." >&2
      echo "       Install XQuartz (brew install --cask xquartz), launch it, then re-enter the shell." >&2
    fi
  '';
}
