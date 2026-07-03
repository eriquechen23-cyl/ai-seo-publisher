<!doctype html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<div class="site-shell">
  <header class="site-header">
    <div class="site-header__inner">
      <a class="brand" href="<?php echo esc_url(home_url('/')); ?>">
        <span class="brand__name"><?php bloginfo('name'); ?></span>
        <span class="brand__tagline">AI generated SEO drafts for WordPress review</span>
      </a>
      <a class="nav-link" href="<?php echo esc_url(admin_url('edit.php?post_status=draft&post_type=post')); ?>">Drafts</a>
    </div>
  </header>
  <main class="site-main">
