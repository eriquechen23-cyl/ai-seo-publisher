<?php get_header(); ?>

<?php if (have_posts()) : ?>
  <?php while (have_posts()) : the_post(); ?>
    <article <?php post_class('article-shell'); ?>>
      <header class="article-hero">
        <div class="article-hero__inner">
          <div class="article-meta">
            Draft preview · <?php echo esc_html(get_the_date()); ?>
          </div>
          <h1 class="article-title"><?php the_title(); ?></h1>
          <p class="article-dek">Generated SEO article draft prepared for editorial review in WordPress.</p>
        </div>
      </header>

      <div class="content-layout">
        <div class="article-content">
          <?php the_content(); ?>
        </div>

        <aside class="sidebar" aria-label="Article workflow details">
          <section class="sidebar-box">
            <span class="sidebar-label">Status</span>
            <h2>Draft Review</h2>
            <p>The post remains unpublished until an editor approves it.</p>
          </section>
          <section class="sidebar-box">
            <span class="sidebar-label">Pipeline</span>
            <h2>AI SEO Publisher</h2>
            <p>FastAPI generated and validated the HTML before submitting it through the WordPress REST API.</p>
          </section>
        </aside>
      </div>
    </article>
  <?php endwhile; ?>
<?php endif; ?>

<?php get_footer(); ?>
