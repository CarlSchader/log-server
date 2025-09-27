{ self, ...  }: {
  nixosModules.default = { config, lib, ... }: 
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

