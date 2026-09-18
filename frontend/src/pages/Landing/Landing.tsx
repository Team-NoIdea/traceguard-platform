import FooterBackground from './footer-background';
import BrandLogo from './brand-logo';
import './landing.css';

export default function Home() {
  return (
    <footer className="tg-landing tg-footer" aria-label="Footer">
      <FooterBackground />
      <div className="tg-jobs">
        <span className="tg-tag">TraceGuard</span>
        <span className="tg-headline tg-job-title">protect your<br />applications</span>
        <div className="tg-footer-nav">
          <span>Scan</span>
          <span>Detect</span>
          <span>Correlate</span>
          <span>Verify</span>
        </div>
      </div>
      <div className="tg-logo" role="img" aria-label="TraceGuard studio mark">
        <BrandLogo />
      </div>
      <div className="tg-contact">
        <span className="tg-tag">evidence first</span>
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