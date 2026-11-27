const drawer = document.querySelector('.docs-drawer');
const compact = matchMedia('(max-width: 48rem)');
const links = [...drawer.querySelectorAll('nav a')];

function setDrawerMode() {
  drawer.open = !compact.matches;
}

function markSection() {
  const target = location.hash || '#quickstart';
  for (const link of links) {
    if (link.hash === target) {
      link.setAttribute('aria-current', 'location');
    } else {
      link.removeAttribute('aria-current');
    }
  }
}

setDrawerMode();
markSection();
compact.addEventListener('change', setDrawerMode);
window.addEventListener('hashchange', markSection);
drawer.addEventListener('click', (event) => {
  if (compact.matches && event.target.closest('nav a')) drawer.open = false;
});
