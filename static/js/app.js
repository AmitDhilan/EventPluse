const clubForm = document.getElementById("clubForm");
const clubNameEl = document.getElementById("clubName");
const clubCoordEl = document.getElementById("clubCoord");
const clubCatEl = document.getElementById("clubCat");

const eventForm = document.getElementById("eventForm");
const eventClubEl = document.getElementById("eventClub");
const eventTitleEl = document.getElementById("eventTitle");
const eventVenueEl = document.getElementById("eventVenue");
const eventDateEl = document.getElementById("eventDate");
const eventCapacityEl = document.getElementById("eventCapacity");
const eventStatusEl = document.getElementById("eventStatus");
const eventDescEl = document.getElementById("eventDesc");

const regForm = document.getElementById("regForm");
const regEventEl = document.getElementById("regEvent");
const studentNameEl = document.getElementById("studentName");
const rollNoEl = document.getElementById("rollNo");
const studentEmailEl = document.getElementById("studentEmail");

const searchInput = document.getElementById("searchInput");
const filterClub = document.getElementById("filterClub");
const filterStatus = document.getElementById("filterStatus");
const regFilterEvent = document.getElementById("regFilterEvent");
const eventsContainer = document.getElementById("eventsContainer");
const regTableBody = document.getElementById("regTableBody");
const themeBtn = document.getElementById("themeBtn");

eventDateEl.value = new Date().toISOString().split("T")[0];

if (localStorage.getItem("ep_theme") === "light") {
  document.body.classList.add("light");
  themeBtn.textContent = "Dark Mode";
}

themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("light");
  const isLight = document.body.classList.contains("light");
  localStorage.setItem("ep_theme", isLight ? "light" : "dark");
  themeBtn.textContent = isLight ? "Dark Mode" : "Light Mode";
});

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function loadClubs() {
  const res = await fetch("/api/clubs");
  const data = await res.json();
  const clubs = data.clubs || [];

  const prevClubFilter = filterClub.value;
  eventClubEl.innerHTML = clubs
    .map((c) => `<option value="${c.id}">${esc(c.name)} (${esc(c.category)})</option>`)
    .join("");

  filterClub.innerHTML =
    '<option value="All">All Clubs</option>' +
    clubs.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");

  if ([...filterClub.options].some((o) => o.value === prevClubFilter)) {
    filterClub.value = prevClubFilter;
  }
}

async function loadEvents() {
  const params = new URLSearchParams({
    search: searchInput.value.trim(),
    club_id: filterClub.value,
    status: filterStatus.value
  });

  const res = await fetch(`/api/events?${params.toString()}`);
  const data = await res.json();

  document.getElementById("statEvents").textContent = data.overview.total_events;
  document.getElementById("statOpen").textContent = data.overview.open_events;
  document.getElementById("statRegs").textContent = data.overview.total_registrations;
  document.getElementById("statCheckedIn").textContent = data.overview.checked_in;

  const events = data.events || [];
  const prevRegEvent = regEventEl.value;
  const prevRegFilter = regFilterEvent.value;

  regEventEl.innerHTML = events
    .map((e) => `<option value="${e.id}">${esc(e.title)} — ${e.seats_left} seats left</option>`)
    .join("");

  regFilterEvent.innerHTML =
    '<option value="">All Events</option>' +
    events.map((e) => `<option value="${e.id}">${esc(e.title)}</option>`).join("");

  if ([...regEventEl.options].some((o) => o.value === prevRegEvent)) {
    regEventEl.value = prevRegEvent;
  }
  if ([...regFilterEvent.options].some((o) => o.value === prevRegFilter)) {
    regFilterEvent.value = prevRegFilter;
  }

  if (!events.length) {
    eventsContainer.innerHTML = '<div class="empty">No matching events found.</div>';
    return;
  }

  eventsContainer.innerHTML = events
    .map(
      (e) => `
      <div class="event-card">
        <div>
          <div class="event-title">${esc(e.title)} <span class="badge st-${esc(e.status)}">${esc(e.status)}</span></div>
          ${e.description ? `<div class="event-desc">${esc(e.description)}</div>` : ""}
          <div class="event-meta">
            <span>Club: <strong>${esc(e.club_name)}</strong></span>
            <span>Venue: ${esc(e.venue)}</span>
            <span>Date: ${esc(e.event_date)}</span>
            <span>Seats: <strong>${e.registered_count}/${e.capacity}</strong> (${e.seats_left} left)</span>
          </div>
        </div>
        <div class="event-actions">
          <select class="mini-select" onchange="changeEventStatus(${e.id}, this.value)">
            <option value="Open" ${e.status === "Open" ? "selected" : ""}>Open</option>
            <option value="Closed" ${e.status === "Closed" ? "selected" : ""}>Closed</option>
            <option value="Completed" ${e.status === "Completed" ? "selected" : ""}>Completed</option>
          </select>
          <button class="btn-del" onclick="removeEvent(${e.id})">Delete</button>
        </div>
      </div>
    `
    )
    .join("");
}

async function loadRegistrations() {
  const evId = regFilterEvent.value;
  const url = evId ? `/api/registrations?event_id=${encodeURIComponent(evId)}` : "/api/registrations";
  const res = await fetch(url);
  const data = await res.json();
  const regs = data.registrations || [];

  if (!regs.length) {
    regTableBody.innerHTML = '<tr><td colspan="5" class="empty">No student registrations yet.</td></tr>';
    return;
  }

  regTableBody.innerHTML = regs
    .map(
      (r) => `
      <tr>
        <td><strong>${esc(r.student_name)}</strong><br><small style="color:var(--muted)">${esc(r.student_email)}</small></td>
        <td>${esc(r.roll_no)}</td>
        <td>${esc(r.event_title)}<br><small style="color:var(--muted)">${esc(r.club_name)}</small></td>
        <td>
          <select class="mini-select" onchange="changeAttendance(${r.id}, this.value)">
            <option value="Registered" ${r.attendance_status === "Registered" ? "selected" : ""}>Registered</option>
            <option value="Checked-In" ${r.attendance_status === "Checked-In" ? "selected" : ""}>Checked-In</option>
            <option value="Absent" ${r.attendance_status === "Absent" ? "selected" : ""}>Absent</option>
          </select>
        </td>
        <td><button class="btn-del" onclick="removeReg(${r.id})">Cancel</button></td>
      </tr>
    `
    )
    .join("");
}

clubForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const res = await fetch("/api/clubs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: clubNameEl.value.trim(),
      coordinator: clubCoordEl.value.trim(),
      category: clubCatEl.value.trim() || "General"
    })
  });
  const data = await res.json();
  if (res.ok) {
    clubNameEl.value = "";
    clubCoordEl.value = "";
    clubCatEl.value = "";
    await loadClubs();
  } else {
    alert(data.error || "Could not add club.");
  }
});

eventForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const res = await fetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      club_id: Number(eventClubEl.value),
      title: eventTitleEl.value.trim(),
      venue: eventVenueEl.value.trim(),
      event_date: eventDateEl.value,
      capacity: Number(eventCapacityEl.value),
      status: eventStatusEl.value,
      description: eventDescEl.value.trim()
    })
  });
  const data = await res.json();
  if (res.ok) {
    eventTitleEl.value = "";
    eventVenueEl.value = "";
    eventDescEl.value = "";
    await Promise.all([loadClubs(), loadEvents()]);
  } else {
    alert(data.error || "Could not publish event.");
  }
});

regForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const res = await fetch("/api/registrations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_id: Number(regEventEl.value),
      student_name: studentNameEl.value.trim(),
      roll_no: rollNoEl.value.trim(),
      student_email: studentEmailEl.value.trim()
    })
  });
  const data = await res.json();
  if (res.ok) {
    studentNameEl.value = "";
    rollNoEl.value = "";
    studentEmailEl.value = "";
    await Promise.all([loadEvents(), loadRegistrations()]);
  } else {
    alert(data.error || "Registration failed.");
  }
});

async function changeEventStatus(id, status) {
  await fetch(`/api/events/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  await loadEvents();
}

async function removeEvent(id) {
  await fetch(`/api/events/${id}`, { method: "DELETE" });
  await Promise.all([loadClubs(), loadEvents(), loadRegistrations()]);
}

async function changeAttendance(regId, attendance_status) {
  await fetch(`/api/registrations/${regId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ attendance_status })
  });
  await loadEvents();
}

async function removeReg(regId) {
  await fetch(`/api/registrations/${regId}`, { method: "DELETE" });
  await Promise.all([loadEvents(), loadRegistrations()]);
}

window.changeEventStatus = changeEventStatus;
window.removeEvent = removeEvent;
window.changeAttendance = changeAttendance;
window.removeReg = removeReg;

searchInput.addEventListener("input", loadEvents);
filterClub.addEventListener("change", loadEvents);
filterStatus.addEventListener("change", loadEvents);
regFilterEvent.addEventListener("change", loadRegistrations);

(async function init() {
  await loadClubs();
  await loadEvents();
  await loadRegistrations();
})();