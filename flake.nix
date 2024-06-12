{
    inputs = {
        nixpkgs.url = github:nixos/nixpkgs/nixos-24.05;
    };
    
    outputs = {nixpkgs, ...}: {
        packages.aarch64-linux = 
        let pkgs = import nixpkgs { system = "aarch64-linux"; };
            callPythonPackage = pkgs.lib.callPackageWith (pkgs // pkgs.python3.pkgs);
        in rec {
            bwrap_devshell = callPythonPackage ./default.nix {};
            default = bwrap_devshell;
        };
    };
}
