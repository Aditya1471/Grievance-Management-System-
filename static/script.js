// Example script for interactivity
document.addEventListener("DOMContentLoaded", () => {
  console.log("🍽 Food Frenzy");

  const year = new Date().getFullYear();
  const footer = document.querySelector("footer p");
  if (footer) footer.innerHTML = `© ${year} 🍽 Food Frenzy | All Rights Reserved`;
});
