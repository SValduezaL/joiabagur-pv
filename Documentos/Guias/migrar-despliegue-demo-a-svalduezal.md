# Plan: trasladar el despliegue de la demo a `SValduezaL/joiabagur-pv`

**Estado:** pendiente de ejecutar · **Redactado:** 2026-09-29

## 1. Situación de partida

El código vive desde el 2026-09-29 en **`SValduezaL/joiabagur-pv`** (`origin`). La demo de AWS
(<https://52-49-209-14.sslip.io>, cuenta `666823181744`, `eu-west-1`) **se sigue desplegando desde
`skydr4g0n-it/joiabagur-pv`** (`upstream`), porque dos cosas de la infraestructura llevan escrito el
nombre del repositorio:

| Dónde | Qué contiene | Fichero |
|---|---|---|
| Confianza del rol `jbg-demo-deploy-role` | `repo:skydr4g0n-it/joiabagur-pv:environment:demo` | [terraform/demo/iam.tf](../../terraform/demo/iam.tf) |
| Parámetro `/jbg-demo/DEPLOYMENT_BUNDLE_URL` | `https://codeload.github.com/skydr4g0n-it/joiabagur-pv/tar.gz/refs/heads/demo` | [terraform/demo/ssm.tf](../../terraform/demo/ssm.tf) |
| `user_data` de la EC2 | la misma URL del paquete, usada solo en el primer arranque | [terraform/demo/ec2.tf](../../terraform/demo/ec2.tf) |

Además, en GitHub:
- `upstream` tiene el Environment `demo` con el secreto `DEMO_DEPLOY_ROLE_ARN`;
- `origin` no tiene Environment, y `deploy-demo.yml` **ni siquiera está registrado**: GitHub no lo
  registra hasta que algún evento lo dispara.

## 2. El riesgo que gobierna todo el plan

**Un `terraform apply` completo con el nuevo `github_repo` reemplaza la instancia.** La URL del paquete
se renderiza en el `user_data`, y la instancia de la demo **no** ignora sus cambios (decisión escrita en
`ec2.tf`). Reemplazarla destruye el volumen raíz, y con él:
- la base de datos (`jbg-demo-pgdata`), con el trabajo copiado el 2026-09-28 (familias, revisiones,
  perfiles e historial de evaluación);
- las copias de seguridad de `/root` (`pre-sync-demo.dump` y `pre-sync-users.sql`);
- el certificado emitido por Caddy. La IP elástica se conserva, así que el nombre no cambia, pero habría
  que volver a emitirlo.

Por eso el plan usa un **apply dirigido** (`-target`) solo a los dos recursos que deben cambiar, y
**nunca** un `apply` completo sin haber hecho antes una copia de la base fuera de la instancia.

## 3. Resultado esperado

- Un push a `origin/demo`, o un lanzamiento manual de `deploy-demo.yml` en `origin`, construye, despliega
  y verifica la demo.
- `upstream` deja de poder desplegar: su token OIDC ya no coincide con la confianza del rol.
- La base de datos, el certificado y la IP de la demo no cambian.

## 4. Pasos

### 4.1 Preparación (sin cambios en AWS)

1. **Sesión AWS:** `aws sso login --profile jbg-demo` y `aws sts get-caller-identity --profile jbg-demo`
   (cuenta `666823181744`).
2. **Copia de seguridad fuera de la instancia.** Si algo sale mal y la instancia se reemplaza, las copias
   de `/root` se pierden con ella:
   - en el anfitrión, `pg_dump -Fc` de `joiabagur_pv` (como en el runbook, §5.9, paso 1);
   - súbela a S3 con una URL prefirmada de subida, o descárgala a la máquina local por el mismo camino, y
     comprueba su tamaño y su `sha256sum`.
3. **Comprobar que `origin/demo` despliega lo mismo que hay ahora.** `git diff --stat upstream/demo
   origin/demo` solo debe listar documentación, los tres workflows retirados y el historial de PR, sin
   ningún fichero de `backend/`, `frontend/`, `ai-service/`, `compose.demo.yaml` ni `deploy/demo/*.sh`. Si
   aparece código, decide antes si ese código debe desplegarse.

### 4.2 Terraform: solo el rol y el parámetro

4. En `terraform/demo/terraform.tfvars` (local, ignorado por git): `github_repo = "SValduezaL/joiabagur-pv"`.
5. **Plan completo, solo para leerlo:** `terraform plan`. Debe mostrar:
   - `aws_iam_role.deploy`: *update in-place* (confianza);
   - `aws_ssm_parameter.deployment_bundle_url`: *update in-place*;
   - `aws_instance.host`: **must be replaced** por `user_data`, junto con la reasociación de la IP.

   Es la confirmación del riesgo del §2. **No se aplica.**
6. **Plan dirigido:**
   ```bash
   terraform plan  -target=aws_iam_role.deploy -target=aws_ssm_parameter.deployment_bundle_url -out=move.tfplan
   ```
   Debe mostrar exactamente **2 to change, 0 to add, 0 to destroy**. Cualquier otra cifra: parar.
7. `terraform apply move.tfplan`.
8. Comprobar:
   - `aws iam get-role --role-name jbg-demo-deploy-role --query Role.AssumeRolePolicyDocument` → `repo:SValduezaL/joiabagur-pv:environment:demo`;
   - `aws ssm get-parameter --name /jbg-demo/DEPLOYMENT_BUNDLE_URL` → la URL de `SValduezaL`.
   - En Git Bash, exporta antes `MSYS_NO_PATHCONV=1`: si no, el `/` inicial del nombre se reescribe como
     una ruta de Windows.

Desde este momento **ningún repositorio puede desplegar** hasta completar el §4.3. Si aparece un problema
aquí, la vuelta atrás es repetir los pasos 4 a 7 con `skydr4g0n-it/joiabagur-pv`.

### 4.3 GitHub: el Environment y el workflow en `origin`

9. Crear el Environment `demo` en `SValduezaL/joiabagur-pv` (*Settings → Environments*) con el secreto
   `DEMO_DEPLOY_ROLE_ARN` = `terraform output -raw deploy_role_arn`. El ARN **no cambia**: es el mismo rol
   con otra confianza. `DEMO_INSTANCE_ID` ya no hace falta: el workflow localiza la instancia por su
   etiqueta.
   ```bash
   gh api -X PUT repos/SValduezaL/joiabagur-pv/environments/demo
   gh secret set DEMO_DEPLOY_ROLE_ARN --env demo -R SValduezaL/joiabagur-pv --body "<arn>"
   ```
   Opcional: restringir el Environment a la rama `demo` (*Deployment branches → Selected branches*).
10. **Registrar `deploy-demo.yml`.** Un push que modifique el fichero hace que GitHub lo registre. Lo más
    limpio es un commit en `ai-eng` que actualice su comentario de cabecera con el nombre del nuevo
    repositorio, subido a `ai-eng` y a `finalproject-SVL`. **No a `demo` todavía**: en `demo`, un cambio en
    ese fichero dispara un despliegue, porque no está en `paths-ignore`.
    Comprobar con `gh workflow list -R SValduezaL/joiabagur-pv --all`.
11. **Primer despliegue, a mano:**
    ```bash
    gh workflow run deploy-demo.yml -R SValduezaL/joiabagur-pv --ref demo
    gh run watch -R SValduezaL/joiabagur-pv
    ```
    El workflow asume el rol por OIDC, construye y sube las dos imágenes a ECR con la etiqueta
    `sha-<commit>`, escribe `IMAGE_TAG`, descarga el paquete desde la URL nueva y ejecuta `deploy.sh` y
    `verify.sh` en el anfitrión. **La base de datos no se toca**: el volumen persiste y `alembic upgrade
    head` no tiene nada pendiente.
12. **Verificar:**
    - el workflow en verde, con las siete condiciones de `verify.sh`;
    - `curl -sI https://52-49-209-14.sslip.io` → 200, con el mismo certificado;
    - como `demo.admin`: tarjeta «Servicio de IA» con 1.167 documentos, **156 familias** en la revisión de
      familias y **204** revisiones en las métricas de perfiles, es decir, los datos del 2026-09-28 siguen
      ahí;
    - una búsqueda con ayuda y una pregunta al agente.

### 4.4 Cierre

13. **Deshabilitar el despliegue en `upstream`**, para que un push allí no deje un workflow en rojo:
    `gh workflow disable deploy-demo.yml -R skydr4g0n-it/joiabagur-pv` (basta con permiso de escritura).
    Si GitHub lo rechaza, pídeselo al dueño del repositorio o déjalo anotado: fallará en OIDC sin tocar
    AWS.
14. **Actualizar la documentación** (commit en `ai-eng` y cherry-pick a `demo`, que es documentación y no
    despliega):
    - `README.md`, §1.4.1: retirar el aviso «la demo publicada se despliega todavía desde skydr4g0n-it»;
    - `deploy/demo/README.md`, §2: dejar el aviso del `-target` como procedimiento general y anotar la
      fecha del traslado;
    - `terraform/demo/terraform.tfvars.example` y `variables.tf`: el ejemplo pasa a `SValduezaL/joiabagur-pv`;
    - la memoria del proyecto (`repo-trasladado-a-svalduezal`): la demo ya despliega desde `origin`.
15. **Decidir qué hacer con la deriva del `user_data`.** Tras el apply dirigido, el estado de Terraform
    sigue proponiendo reemplazar la instancia. Hay tres opciones:
    - **(a) Dejarla y documentarla** (recomendada mientras la demo tenga datos que conservar): cualquier
      `apply` futuro debe ir con `-target` o precedido de una copia de la base fuera de la instancia.
    - (b) Añadir `lifecycle { ignore_changes = [user_data] }` a `aws_instance.host`. Elimina la deriva,
      pero contradice la decisión escrita en `ec2.tf`: el repositorio dejaría de ser la fuente de verdad
      del aprovisionamiento.
    - (c) Reemplazar la instancia a propósito, en una ventana planificada, y restaurar la base desde la
      copia del paso 2 (runbook §5). Es lo más limpio para Terraform y lo más caro en trabajo.

## 5. Vuelta atrás

| Fallo en | Cómo se deshace |
|---|---|
| §4.2 (Terraform) | Pasos 4 a 7 con `github_repo = "skydr4g0n-it/joiabagur-pv"`, siempre con `-target` |
| §4.3 (despliegue en rojo) | El contenedor anterior sigue en marcha salvo que `deploy.sh` haya llegado a reemplazarlo. Para volver a la imagen previa: `gh workflow run deploy-demo.yml --ref demo -f image_tag=sha-<commit-anterior>`, con el `IMAGE_TAG` que había en SSM antes del paso 11 |
| Base de datos dañada | `pg_restore --clean` desde la copia del paso 2 y después `sync --full` (runbook §5.9) |
| Instancia reemplazada por error | Restaurar la base desde la copia del paso 2 siguiendo el runbook §5 (el `bootstrap.sql` y los drenajes incluidos) |

## 6. Lo que este plan no hace

- No toca la pila de producción del MVP (`terraform/`, en otra cuenta).
- No cambia la cuenta AWS, la IP, el dominio ni los secretos de SSM.
- No mueve la etiqueta `v1.0-final-SVL`.
