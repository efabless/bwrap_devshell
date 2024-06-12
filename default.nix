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
  
  meta = {
    mainProgram = "bwrap_devshell";
  };
}
