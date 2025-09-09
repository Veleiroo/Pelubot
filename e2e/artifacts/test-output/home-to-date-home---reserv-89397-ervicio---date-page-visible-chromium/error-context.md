# Page snapshot

```yaml
- generic [ref=e2]:
  - region "Notifications alt+T"
  - generic [ref=e4]:
    - heading "Se produjo un error en la interfaz" [level=1] [ref=e5]
    - paragraph [ref=e6]: Prueba a volver atrás o ir al inicio.
    - generic [ref=e7]:
      - link "Inicio" [ref=e8] [cursor=pointer]:
        - /url: /
      - link "Debug" [ref=e9] [cursor=pointer]:
        - /url: /debug
    - generic [ref=e10]: "Error: A <Select.Item /> must have a value prop that is not an empty string. This is because the Select value can be set to an empty string to clear the selection and show the placeholder."
```