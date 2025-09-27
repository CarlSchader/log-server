{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ...  }: 
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        packages.default = pkgs.python312.pkgs.buildPythonPackage {
          pname = "log-server";
          version = "0.1.0";
          src = ./.;
          pyproject = true;

          propagatedBuildInputs = with pkgs.python312.pkgs; [
            fastapi
            pyjwt
            uvicorn
          ];

          build-system = with pkgs.python312.pkgs; [
            setuptools
            wheel
          ];
        };

        apps."${system}".default = {
           type = "app";
           protram = "${self.packages.${system}.default}/bin/log-server";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            uv
            jwt-cli
          ];

          shellHook = ''
            export JWT_SECRET=dev-secret
            export JWT=$(jwt encode --secret $JWT_SECRET --alg HS256 --payload sub="carl")
          '';
        };

        nixosModules.default = { config, pkgs, ... }: 
        let
          cfg = config.services.log-server;
        in {

        };
      }
    );
}
