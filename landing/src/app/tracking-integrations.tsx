"use client";

import Image from "next/image";
import { ArrowUpRight } from "lucide-react";
import CopyButton from "./copy-button";

const destinations = [
  { id: "obsidian", name: "Obsidian", instruction: "Connect to a dedicated folder in my Obsidian vault using Markdown files. Create one note per application and an overview, preserving my personal notes and vault settings." },
  { id: "notion", name: "Notion", instruction: "Connect to a Notion application tracker. Help me choose or create a dedicated destination, authorize access, and map its properties while preserving my personal page content." },
  { id: "googlesheets", name: "Google Sheets", instruction: "Connect to a Google Sheets application tracker. Guide local browser authorization, choose a spreadsheet and tracker tab, and map columns while preserving custom columns and formulas." },
  { id: "airtable", name: "Airtable", instruction: "Connect to an Airtable application tracker. Help me select a base and editable table, authorize only the needed access, and map fields while preserving formulas, linked records, and custom fields." },
  { id: "hubspot", name: "HubSpot", instruction: "Connect to a HubSpot application tracker. Verify my account's supported objects and API access, help me select a dedicated deal pipeline or an approved available object, and map application stages while preserving existing CRM records. Do not assume paid custom objects are available or trigger outreach and sales automations." },
  { id: "gohighlevel", name: "GoHighLevel", logo: "gohighlevel.png", instruction: "Connect to GoHighLevel (GHL) for application tracking. Guide me through the correct sub-account and scoped authorization, choose a dedicated opportunity pipeline, and map stages and required contact associations. Never invent contacts, merge applications that share a contact, or trigger messaging, campaigns, and outreach automations." },
];

const calendars = [
  { id: "googlecalendar", name: "Google Calendar", logo: "googlecalendar.svg" },
  { id: "outlook", name: "Outlook", logo: "outlook.svg" },
];

function calendarPrompt(name: string) {
  return `Use the cv-calendar skill at .agents/skills/cv-calendar/SKILL.md in this CV Tailor checkout. Connect ${name} for my job interviews, application deadlines, and follow-up reminders. Load preferences get first and reuse matching saved setup. Help me choose a calendar, timezone, and reminders; ask for missing dates and interview times rather than guessing. Keep SQLite as my primary application tracker and use one-way, manual calendar publishing. Prepare reusable local setup and publish scripts with a dry run before the first publish. Use stable event IDs so retries and rescheduling do not create duplicates, preserve personal notes, and stop on conflicting calendar edits. Save this provider and its nonsecret setup-file path in calendar_connections using preferences set with its current revision, preserving my other calendar and tracking connections. Guide browser authorization locally; use scripts/integration_env.py for hidden credential entry and save credentials only in the Git-ignored .env.integrations file after verifying it is untracked and ignored. Never ask me to paste credentials into agent chat. Connecting alone must not create events, invite attendees, send email, or enable background syncing.`;
}

function setupPrompt(instruction: string) {
  return `Use the cv-connect skill at .agents/skills/cv-connect/SKILL.md in this CV Tailor checkout. ${instruction} Keep SQLite as my primary tracking database and use one-way publishing only. Load preferences get first and reuse matching saved setup. Remember this provider and the nonsecret setup-file path in SQLite using preferences set with its current revision, so future sessions can resume it. Ask for missing destination and field choices, then guide me through setup with reusable local setup and publish scripts. If credentials are needed, have me enter them locally through hidden prompts using scripts/integration_env.py and save them in the Git-ignored .env.integrations file. Verify that file is untracked and ignored before saving. Never ask me to paste credentials into agent chat or include them in prompts, logs, or published data. Show a dry run before the first publish, use stable application IDs to avoid duplicates, and keep syncing manual unless I request otherwise.`;
}

export default function TrackingIntegrations() {
  return <section className="tracking-integrations section" id="integrations" aria-labelledby="integrations-title">
    <div className="section-heading"><div><span className="eyebrow">YOUR DATA. YOUR TOOLS.</span><h2 id="integrations-title">Connect it anywhere.</h2><a className="text-link integration-setup-link" href="https://github.com/yabswannalearn/CV-Tailor/tree/main/.agents/skills/cv-connect" target="_blank" rel="noreferrer">Explore the setup skill<ArrowUpRight size={13} /></a></div></div>
    <div className="integration-grid">
      {destinations.map(destination => <article className="integration-card" key={destination.id}>
        <div className="integration-logo"><Image className={destination.id === "gohighlevel" ? "integration-logo-padded" : undefined} src={`/integrations/${destination.logo || `${destination.id}.svg`}`} alt={`${destination.name} logo`} width={49} height={49} /></div>
        <h3>{destination.name}</h3>
        <CopyButton text={setupPrompt(destination.instruction)} label={`Copy ${destination.name} connection prompt`} caption="Copy prompt" />
      </article>)}
      {calendars.map(calendar => <article className="integration-card" key={calendar.id}>
        <div className="integration-logo"><Image src={`/integrations/${calendar.logo}`} alt={`${calendar.name} logo`} width={49} height={49} /></div>
        <h3>{calendar.name}</h3>
        <CopyButton text={calendarPrompt(calendar.name)} label={`Copy ${calendar.name} connection prompt`} caption="Copy prompt" />
      </article>)}
    </div>
  </section>;
}
