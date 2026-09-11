import './App.css'

function App() {
  return (
    <main className="app-shell">
      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="/" aria-label="MUJX Hackathon Maker home">
          <span className="brand-mark">M</span>
          <span>MUJX <strong>Hackathon Maker</strong></span>
        </a>
        <span className="status-pill">Maker workspace</span>
      </nav>

      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">MUJX / BUILD TOGETHER</p>
        <h1 id="hero-title">Turn bold ideas into <em>real builds.</em></h1>
        <p className="hero-copy">
          The home for MUJX makers to shape ideas, find collaborators, and launch
          meaningful hackathon projects.
        </p>
        <div className="hero-actions">
          <button className="primary-button" type="button">Start making <span aria-hidden="true">&#8594;</span></button>
          <button className="text-button" type="button">Explore projects <span aria-hidden="true">&#8599;</span></button>
        </div>
      </section>

      <section className="feature-strip" aria-label="Maker workspace features">
        <article>
          <span className="feature-number">01</span>
          <h2>Shape the spark</h2>
          <p>Give your idea a clear direction and a place to grow.</p>
        </article>
        <article>
          <span className="feature-number">02</span>
          <h2>Find your crew</h2>
          <p>Bring the right minds together around a shared challenge.</p>
        </article>
        <article>
          <span className="feature-number">03</span>
          <h2>Make it matter</h2>
          <p>Move from a rough concept to something people can use.</p>
        </article>
      </section>
    </main>
  )
}

export default App
