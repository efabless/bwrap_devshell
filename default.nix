{
  buildPythonPackage,
  python3,
  click,
  zstandard,
  rich,
  poetry-core,
}:
buildPythonPackage {
  name = "bwrap_devshell";
  version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).tool.poetry.version;
  format = "pyproject";
  src = ./.;

  nativeBuildInputs = [poetry-core];
  propagatedBuildInputs = [click zstandard rich];

  meta = with lib; {
    description = "Bubble-wraps a numtide/devshell for deployment in exotic environments";
    mainProgram = "bwrap_devshell";
    license = licenses.asl20;
    platforms = platforms.linux;
  };
}
