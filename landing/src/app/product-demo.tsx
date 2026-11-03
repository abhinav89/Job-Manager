import styles from "./product-demo.module.css";

export default function ProductDemo() {
  return <section className={`${styles.section} section`} id="watch" aria-labelledby="demo-title">
    <div className={styles.copy}>
      <h2 id="demo-title">See your agent at work.</h2>
      <a className="text-link" href="#workflow">Explore the steps below</a>
    </div>
    <figure className={styles.player}>
      <video controls playsInline preload="none" poster="/videos/cv-tailor-explainer-poster.jpg" width={1920} height={1080} aria-label="CV Tailor explainer video">
        <source src="/videos/cv-tailor-explainer.mp4" type="video/mp4" />
        <a href="/videos/cv-tailor-explainer.mp4">Watch the CV Tailor explainer video</a>.
      </video>
    </figure>
  </section>;
}
