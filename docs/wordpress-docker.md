# Local WordPress With Docker

This project uses plain `docker run` commands because the current machine has Docker CLI but no `docker compose` plugin.

完整前後端啟動流程請看 [startup-guide.md](startup-guide.md)。

Start or install WordPress:

```powershell
.\scripts\start-wordpress.ps1
```

Default URLs:

- Site: `http://localhost:8080`
- Admin: `http://localhost:8080/wp-admin`
- REST API: `http://localhost:8080/wp-json/wp/v2`

Default admin credentials:

```text
username: demo_admin
password: demo_password_12345
```

The script creates:

- Docker network: `ai-seo-wordpress-net`
- MariaDB container: `ai-seo-wordpress-db`
- WordPress container: `ai-seo-wordpress`
- MariaDB volume: `ai_seo_wordpress_db`
- WordPress files volume: `ai_seo_wordpress_data`

It also creates a WordPress Application Password and writes it to `backend/.env`.

The script installs the local preview theme from `wordpress/themes/ai-seo-demo` and activates it as `AI SEO Demo`. This changes only the front-end theme layer under `wp-content/themes`; it does not modify WordPress core files.

Stop WordPress:

```powershell
docker --config .docker stop ai-seo-wordpress ai-seo-wordpress-db
```

Start again:

```powershell
docker --config .docker start ai-seo-wordpress-db ai-seo-wordpress
```
