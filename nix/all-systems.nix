{ self, nixpkgs, flake-utils, ...  }: 
  flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };
    in
    {
      packages.default = pkgs.python312.pkgs.buildPythonPackage {
        pname = "log-server";
        version = "0.1.0";
        src = ../.;
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

      nixosModules.default = { config, pkgs, lib, ... }: 
      let
        cfg = config.services.log-server;
      in with lib; {
        options.services.log-server = {
          enable = mkOption {
            type = types.bool;
            default = false;
            description = "Enable log-server service";
          };

          port = mkOption {
            type = types.int;
            default = 8080;
            description = "Port for the log-server to listen on";
          };

          host = mkOption {
            type = types.str;
            default = "0.0.0.0";
            description = "Host for the log-server to bind to";
          };

          jwt-secret = mkOption {
            # required with no default
            type = types.str;
            description = "JWT secret for authentication";
          };
          
          jsonl-file = mkOption {
            type = types.str;
            default = "/var/log/log-server/logs.jsonl";
            description = "Path to the JSONL log file";
          };
        };

        config = mkIf cfg.enable {
          assertions = [
            {
              assertion = cfg.jwt-secret != null;
              message = "services.log-server.jwt-secret must be set if log-server is enabled";
            }
          ];

          systemd.services.log-server = {
            description = "log-server service";
            after = [ "network.target" ];
            wantedBy = [ "multi-user.target" ];
            serviceConfig = {
              ExecStart = "${self.packages.${system}.default}/bin/log-server --host ${cfg.host} --port ${toString cfg.port} --jwt-secret ${cfg.jwt-secret} --jsonl-file ${cfg.jsonl-file}";
              Restart = "on-failure";
              RestartSec = "5s";
            }; 
          };
        };
      };
  }
)

