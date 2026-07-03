<?php get_header(); ?>

<section class="hero">
  <div class="hero__copy">
    <span class="eyebrow">Content Operations Preview</span>
    <h1>AI SEO Publisher Demo</h1>
    <p>Generated SEO drafts are collected here for editorial review before publishing.</p>
  </div>
  <aside class="hero__panel" aria-label="Demo workflow summary">
    <div class="metric">
      <strong>01</strong>
      <span>React form sends article requirements</span>
    </div>
    <div class="metric">
      <strong>02</strong>
      <span>FastAPI generates and validates HTML content</span>
    </div>
    <div class="metric">
      <strong>03</strong>
      <span>WordPress stores the result as a draft</span>
    </div>
  </aside>
</section>

<section class="post-list">
  <?php if (have_posts()) : ?>
    <?php while (have_posts()) : the_post(); ?>
      <article <?php post_class('post-teaser'); ?>>
        <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
        <p><?php echo esc_html(get_the_excerpt()); ?></p>
        <a class="nav-link" href="<?php the_permalink(); ?>">Read preview</a>
      </article>
    <?php endwhile; ?>
  <?php else : ?>
    <article class="post-teaser">
      <h2>No drafts yet</h2>
      <p>Create an article from the React app, then open the generated WordPress preview here.</p>
    </article>
  <?php endif; ?>
</section>

<?php get_footer(); ?>
