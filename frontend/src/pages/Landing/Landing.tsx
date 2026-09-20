import { Link } from 'react-router-dom';
import FooterBackground from './footer-background';
import './landing.css';

export default function Home() {
  return (
    <footer className="tg-landing tg-footer" aria-label="Footer">
      <FooterBackground />
      <div className="tg-jobs">
        <span className="tg-tag">TraceGuard</span>
        <span className="tg-headline tg-job-title">protect your<br />applications</span>
        <div className="tg-footer-nav">
          <Link to="/login">Start scan</Link>
          <span>Detect</span>
          <span>Correlate</span>
          <span>Verify</span>
        </div>
      </div>
      <div className="tg-scan-cta">
        <Link className="tg-start-scan" to="/login" state={{ from: '/scans/new' }}>
          Start Scan
          <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </Link>
      </div>
      <div className="tg-contact">
        <Link className="tg-tag" to="/login">Sign in</Link>
        <div className="tg-headline tg-contact-links">
          <span>find the risks.</span>
          <span>verify your fixes*</span>
        </div>
        <p className="tg-note">*scan. correlate. test. review with confidence.</p>
        <div className="tg-socials">
          <span aria-label="LinkedIn"><img src="/linkedin.svg" alt="" width="35" height="35" /></span>
          <span aria-label="Instagram"><img src="/instagram.svg" alt="" width="35" height="35" /></span>
          <span aria-label="TikTok"><img src="/tiktok.svg" alt="" width="35" height="35" /></span>
        </div>
      </div>
    </footer>
  );
}