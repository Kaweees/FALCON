{
  pkgs ? import <nixpkgs> { config.allowUnfree = true; },
}:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311 # Python 3.11
    uv # Python package manager
    nixfmt # Nix formatter
    just # Just runner
    pkg-config
    cmake # Required for cyclonedx build
    cyclonedds # CycloneDX C++ library
    stdenv.cc.cc.lib # C++ standard library for NumPy/MuJoCo
    zlib # Compression library often needed by numpy/pandas
    glib # General utility library
    wayland # Wayland libraries for GLFW
    libGL # OpenGL libraries
    xorg.libX11 # X11 libraries
    libxkbcommon # XKB common library for GLFW
    libglvnd # OpenGL vendor neutral dispatch library
    mesa # Mesa OpenGL implementation
    pixi
    micromamba
  ];

  # Shell hook to set up environment
  shellHook = ''
    export CYCLONEDDS_HOME=${pkgs.cyclonedds}
    export CMAKE_PREFIX_PATH="$CYCLONEDDS_HOME:$CMAKE_PREFIX_PATH"
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.glib}/lib:${pkgs.wayland}/lib:${pkgs.libGL}/lib:${pkgs.xorg.libX11}/lib:${pkgs.libxkbcommon}/lib:${pkgs.libglvnd}/lib:${pkgs.mesa}/lib:$CYCLONEDDS_HOME/lib:$LD_LIBRARY_PATH"
    export WAYLAND_DISPLAY=${if builtins.getEnv "WAYLAND_DISPLAY" != "" then builtins.getEnv "WAYLAND_DISPLAY" else "wayland-0"}
    export LIBGL_ALWAYS_SOFTWARE=1
    export MESA_GL_VERSION_OVERRIDE=3.3

    export CFLAGS="-DKEY_ALL_APPLICATIONS=0 \
      -DKEY_LINK_PHONE=0 \
      -DKEY_REFRESH_RATE_TOGGLE=0 \
      -DKEY_DICTATE=0 \
      -I$CYCLONEDDS_HOME/include/idlc $CFLAGS"    export UV_PYTHON="${pkgs.python311}/bin/python"
    export TMPDIR=/tmp
  '';
}
