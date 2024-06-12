{
  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-24.05;
  };

  outputs = {nixpkgs, ...}: {
    packages = nixpkgs.lib.genAttrs ["x86_64-linux" "aarch64-linux"] (system: let
      pkgs = import nixpkgs {inherit system;};
      callPythonPackage = pkgs.lib.callPackageWith (pkgs // pkgs.python3.pkgs);
    in rec {
      bwrap_devshell = callPythonPackage ./default.nix {};
      default = bwrap_devshell;
    });
  };
}
