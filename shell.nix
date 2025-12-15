{
  pkgs ? import <nixpkgs> { config.allowUnfree = true; },
}:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    uv
    nixfmt
    just
    pkg-config
    cmake
    cyclonedds
    stdenv.cc.cc.lib
    zlib
    glib
    pixi
    micromamba
  ];

  shellHook = ''
    export CYCLONEDDS_HOME=${pkgs.cyclonedds}
    export CMAKE_PREFIX_PATH="$CYCLONEDDS_HOME:$CMAKE_PREFIX_PATH"

    # Only add CycloneDDS to LD_LIBRARY_PATH – NOT GL/X stuff
    export LD_LIBRARY_PATH="$CYCLONEDDS_HOME/lib:$LD_LIBRARY_PATH"

    # Drop the forced Wayland/GL overrides for now
    # export WAYLAND_DISPLAY=...
    # export LIBGL_ALWAYS_SOFTWARE=1
    # export MESA_GL_VERSION_OVERRIDE=3.3

    export CFLAGS="-I$CYCLONEDDS_HOME/include/idlc $CFLAGS"
    export UV_PYTHON="${pkgs.python311}/bin/python"
    export TMPDIR=/tmp
  '';
}

