# 🔥 DER Tech Review - Meeting Transcript
**Date:** September 10, 2025 at 09:58 CDT  
**Duration:** 56 minutes 13 seconds  
**Participants:** Darrell Reading & Dr. Joe Dorn  
**Location:** Google Meet (with captions enabled)

---

## Meeting Summary

### Key Topics Discussed:
1. **SAG Resource AI Bot Development** - Integration with Productive.io API
2. **Claude Code Quality Issues** - Stub code generation problems  
3. **Meeting Schedule** - Settled on Wednesdays at 9 AM CDT
4. **Google Drive Integration** - Sharing meeting recordings for AI analysis
5. **Cherokee Tribal Infrastructure** - Memory optimization and context management
6. **Hardware Discussion** - Mac Studio capabilities (128GB-512GB RAM)
7. **Inter-tribal Communication** - Telegram bot bridge between Cherokee and BigMac councils

### Action Items:
- ✅ Fix SAG bot to use actual API calls instead of stub responses
- ✅ Move Python scripts to SAG Resource AI subfolder in QDAD apps
- ✅ Set up Google Drive access for meeting recordings
- ✅ Establish Wednesdays 9 AM as regular meeting time
- ✅ Create inter-council Telegram communication channel
- 🔄 Optimize Cherokee thermal memory to reduce context burn
- 🔄 Get BigMac (Mac Studio) integrated into tribal ecosystem via Docker

---

## Full Transcript

### [00:00 - 00:27] Opening - Dogs and Friends
**Darrell:** Okay. I'm getting the couple treats. When stays a special day for him because we go see friends. Oh yeah. We go over the wettakers and let the dog out. That's his friends.

**Dr. Joe:** Gotcha. Nice.

### [00:27 - 01:05] Recording Setup
**Dr. Joe:** I'm just FYI did just start up recording. I'm trying to, I guess I just didn't set up this meeting right, but I'm trying to have every meeting recorded with the, what is it? Include captions in the recording. Yeah. So that I can later go back in and extract that out with AI to make some to-do's and stuff like that. I haven't quite got that workflow figured out yet, but yeah.

### [01:05 - 02:00] Claude Code Issues Discussion
**Darrell:** Yeah. In many ways. So I've watched an interesting video yesterday the day before. Now I'm talking about how people using Claude code are basically getting shenanigans by Claude. Yeah. And I think that may be kind of where some of our problems with some code that it builds basically the whole stub code thing because I spent all yesterday afternoon after you got that code committed pushed up to the repository kind of browsing through and actually let me see can I share it here.

### [02:00 - 03:30] Stub Code Problem Analysis
**Dr. Joe:** But it's doing exactly what we're asking it to do, not anything more. Yeah. And it's not, it's building out a thing, but the thing really is... I might have to, well, that I don't need to share out. But really, in looking through all of the code, it's mostly really still just stub code.

**Darrell:** Like if I... So I figured that it wrote some stub, but what I'm what I have been really good at with with Claude and the tribe is once we start using it and say, hey, look, idiot, this is going wrong. And also, I didn't tell it to alter a thing. So that's bad on me. You need to either tell it to think or alter a thing or, you know, so that's kind of how I've written code is I've just let it write it stub and then show that it's not working and show examples and then prompt it along from there.

### [03:30 - 05:00] SAG Bot Implementation Details
**Dr. Joe:** Yeah. Okay, yeah, because I kind of demonstrated it in a couple things that I put into, is it telegram?

**Darrell:** Yeah, okay. Let me bring that up in a different window.

**Dr. Joe:** So really, when you do something like plug-in slash SAG and actually, I didn't dig into why the help command didn't do anything. But really, all it's doing is just sending a can response back. That says, okay, well, when you plug-in slash SAG, what is it? It's run the SAG underscored command and really, what it does is it just does message reply with SAG response, which SAG response is just a variable that once it's fleshed out would be something coming back from the language model processor, right? And passing that back into the user. Right now, again, it's just, what is it? Where's SAG? Yeah, SAG response is just what you see in that telegram there, where it's like training details, available times, blah, blah, blah, that whole thing. So yeah, we definitely need to kind of get it to start flushing some of those things out on that front.

### [05:00 - 06:30] API Integration Discussion
**Dr. Joe:** So I see that it does have, and I need to just, I need to arrange my windows a little better. So I can see all the things. Yeah. Yeah. So that is that out. I mean, I see that it has like a token, the bot token in there. It's actually using that when it's listening. But yeah, some of those things need fleshed out.

**Darrell:** So one of the things, so my, to be open-ended, right? It needs to be open-ended. Yeah. Yeah, like if it's, if it's going to do something like actually perform the SAG, and there's cork to me, I'm right, which I guess probably the best way to do that would be to just have it start working on that dirt, their pot of bot responder, right?

### [06:30 - 07:30] Code Organization
**Dr. Joe:** I think the token is, the token is for Telegram. It's not for API integration with the SAG stuff. So I guess send SAG response, there might be a need to be a run SAG query, and a couple other things. 

Oh, and a quick note, you might have it clean up, because it started throwing all these Python scripts into the root of the QDAD apps folder. And we probably want to segregate all that down into the SAG resource AI subfolder of QDAD apps, right?

### [07:30 - 09:00] Google Drive Meeting Recordings
**Darrell:** Yeah. So are you capturing our audio right now and captioning it?

**Dr. Joe:** Uh, it is supposed to be. Let me go and double check, manage recording. So yes, it is including captions in the recording. So, like I should be able to share out. I actually have might be something for us to check. Maybe it's not on this call on on another call, but I should be able to share out. So if I go to correct Google, because you're on Google, right? I forget Google, you have a regular Google account. I think that's what I invited you to, right?

**Darrell:** Yeah.

**Dr. Joe:** Okay. Let me see if I can do my drive, meet recordings, and share people, let's hear, yeah, D-Read, gmail.com.

**Darrell:** Yeah, that's me. D-Read, has Patrick, he's called me D-Read. D-Read, D-Read. Yeah, got to throw that eye in there.

### [09:00 - 10:30] Personal Interlude & Sharing Setup
**Darrell:** By the way, I got a new bike.

**Dr. Joe:** Oh, really?

**Darrell:** Bicycle. Oh, bicycle. Awesome. Yeah. Yeah, I gotta be, I don't be good for Canada.

[Various technical discussion about sharing Google Drive access and permissions]

### [10:30 - 12:00] Accessing Shared Recordings
**Dr. Joe:** So you, you will probably have to give them access. I've done, I've done it with, uh, uh, uh, N8N, giving access for an application to access my, like, my email, my drive, and things like that. Yeah. Um, but I just shared with you meet recordings.

**Darrell:** I mean, you can go to drive.google.com also and you can go into shared with me, I think.

**Dr. Joe:** So you, uh, you probably got a notification in your email, but you could probably also go to drive.google.com. Okay. And then there is a shared with me on the left side, um, or it'll, it'll show up in my drive or home also, I think.

### [12:00 - 13:30] AI Analysis Plan
**Dr. Joe:** So theoretically, you should just be able to, uh, get them, uh, ooft over to it, over to Google Drive and say, hey, go and look at the, uh, meet recordings, folders shared with me by Joe or Dr. Joe or whatever. Yeah. And that gives me a giggle every time I see that by the way.

**Darrell:** And to them, you're a shaman.

**Dr. Joe:** I'm a shaman. Nice. Yeah. And their fans of you, I think.

**Darrell:** What's that? I think their fans of you.

**Dr. Joe:** Oh, okay. Cool.

### [13:30 - 17:00] Daily Schedule Discussion
**Darrell:** So Joe, um, typically, um, with the trading environment, I'm not angry to it, but it has kind of set my schedule. So, uh, every morning, uh, I get up and I check things before 8 o'clock to see where the markets, what the markets are doing, check the news blah, blah, blah, uh, for more than just trading. So I do that and I work into, uh, so 10 o'clock, 10 to 11 is power hour. It's a power hour or trading, not necessarily crypto, but for trading in general. So I might watch it from 10 to 11.

**Dr. Joe:** Mm-hmm. Okay.

**Darrell:** We, um, so, oh, go ahead, sorry. Anyway, my schedule is somewhere around. I work from like 7 to 10. And then I take a break. Most of the times from, um, I do work out from 10 to maybe 1 somewhere in that neighborhood. I take my lunch hour there, which is 3 hours. Um, but I'm around. I'm close by. So I'm not out of the office out of my office at that time, but I'm um, looser. You need, you need to, you need to be focused during certain times. And then later on, your flexibility is right.

### [17:00 - 19:00] Meeting Schedule Agreement
**Dr. Joe:** So what's a good timeframe for like these meetings? So, um, I know initially Erica had had kind of said Mondays, we kind of settled on Mondays at 10 o'clock or whatever in the morning. Um, which for me, yeah, I mean, it's fine, but I'd rather like spend Monday and or Tuesday kind of like trying to wrap up things that I should have kind of finished it up by the next sprint start time or whatever. Right. Um, so I think for me, either Tuesday or more likely Wednesday from a day perspective for me is probably good. Um, and come Wednesday, 9 a.m., I should be kind of spun up enough that I can just hop on a call at 9 or whatever.

**Darrell:** What works for you from that respect? I know, um, the last couple meetings we've gone two and a half, three and a half, four and a half hours. Yeah. Which I'm, I'm perfectly fine with, except four on Wednesdays, um, about 11 o'clock. I take off and go and meet Russell for lunch.

**Dr. Joe:** So okay. Well, let's say going forward that Wednesdays at 9 a.m.

**Darrell:** Okay, and that gives an hour for us to kind of heads down, focus on things together.

### [19:00 - 20:30] Recent Code Updates
**Dr. Joe:** Cool. And I'm, oh, good head. I am a dog with a bone. Let's see, added real sag assistant class with the actual API calls, removed all canned sag response text, built natural language API query converter, added real time data fetching methods, granted intelligent response system. Nice.

**Darrell:** Yeah. So when you, when you prod it yesterday, did it actually do the push to the GitHub or did you have to, uh, yeah, it, it, okay, I must it. I don't know why it didn't do that. It committed, but it didn't push anything up.

### [20:30 - 23:00] Context Management Discussion
**Dr. Joe:** So in times in the past, sometimes I've done the push and sometimes it's done the push. It usually either tells me, hey, I'm going to do the push or hey, you do the push. Here's where you run the command because the directory structure. So, but this last time, I just assumed that it did it because it didn't ask me anything.

**Darrell:** So that was one of the other things in that video I watched. I might have to send it over to you, but I think it might have been that one or another one was context, actually, it's a different video I'm thinking of. Context, especially for something that's like, I agentic and stuff like that, um, kind of needs to be refreshed every time you want it to do a thing. So like the context of always commit and always push changes after you make major code changes. Would be part of those memory bits that you want to feed back into it.

### [23:00 - 25:00] Thermal Memory System
**Darrell:** What I'm trying to do though is I'm trying to build that into the tribes thermal memory. Not in a document. So that it's just it does it like autonomically. Dynamically updating dynamically. The majors have to be something that I have a train on other things.

**Dr. Joe:** Yeah, here's here's part of the problem Joe. Part of the problem is is that I've allowed myself to get distracted with this trading shed. Which is fine, which is fine. It has its right. I think I've actually heard the tribal a little bit. It's still from the split bring I know.

### [25:00 - 27:00] Infrastructure Distribution
**Darrell:** So so far, in that with that in mind, it has set red bin as the trader. Mm-hmm. The trader node and there are LLMs that are trade specific running on that machine. There's another one. I'm blue thin. One process. And outside or over there, I moved it over there. So it goes, I have it called the inner once in a while. Then blue thin is my database. And legal, tribe, business. Over there. And Gemini is behind me. And this machine is just the blue that keeps it all running together.

### [27:00 - 29:00] Context Burn Issue
**Darrell:** So the biggest issue that I have right now is that with the way I've been creating it, I've burned through my context for Claude. So and I've got to tell it not to burn through its context and use its thermal memory when needed. What I'm trying to find, what I'm trying to develop is like least effort. Mm-hmm. In the memory. It's what I'm trying to do. At least effort. Yeah. It's it's doing a little bit of work on the memory, but it's not spending a lot of tokens to manage the memory. That's that's the that's what I'm trying to do.

### [29:00 - 31:00] Claude's Design Philosophy
**Darrell:** And and the way I've got this thing designed, it's designed like Claude in production out there in the real world. I wonder if I came up with the idea originally and Claude stole my idea or did Claude already have this designed and as I prodded it along, it barked out what it knew, how with the tribe, how it functions in that environment.

**Dr. Joe:** Yeah. Yeah. I mean, it could be either really. I wouldn't be surprised if part of Claude's poor training gets that kind of feedback loop from all the things that are happening with all the different users out there over time.

### [31:00 - 33:00] Testing SAG Bot
[Discussion about testing the SAG bot with queries and seeing stub responses]

**Dr. Joe:** So that that's an example. Yeah of one of those queries, right? That should start prompting it to execute those model queries on the back end to try and leverage that API into the productive tool. Or theoretically, that's, I mean, that's or this particular environment that we've created for it. That's kind of what I would think we would do.

### [33:00 - 35:00] Bot Duplication Issue
**Darrell:** Well, I just found out that it had multiple, I told it that it had a bot out there running. If you steal the code as it needed and update the code, you do not create a new bot and it created a new God damn bot.

**Dr. Joe:** And part of that could be back into that whole context thing and the general problem that people have said it like more recently, like in the last two or three weeks, the quality of what Claude has been doing has been doing this. It's been going down and people have complained about it and a lot of people are like, yeah, I'm not going to use Claude for a while until they get that shit fixed.

### [35:00 - 37:00] Google Meet Integration Plans
**Dr. Joe:** So now that now that you're going to start plugging in things like the the Google meet recordings folder. Yeah. And set a loose on transcribing and then say, okay, well, come up with a list of tasks that I'm going to review and approve or reject. Right. Ignore the jabbering on about bath trip and so forth and focus on the conversations on technical information dealing with the side project and others.

### [37:00 - 39:00] Memory Optimization Strategy
**Darrell:** I've been well, I told you about some of the shit that I've done with the tribe and I told that that I was very disappointed in it. And then took ownership of the issue and it was very happy that I did that and that it rallied the the tribe to do better. I'm just Walmart. I just Walmart management my tribe just now.

**Dr. Joe:** Yeah, I remember that conversation with King Gish. Yeah. I came in after I had a failed change and my manager and I went in there and Ken said, Darrell, I see that this change didn't go in well. And I see your CEO, we obviously son. I failed you and then he would go into his field.

### [39:00 - 41:00] API Credentials & Memory Recall
**Dr. Joe:** It's saying that I need the API credentials. Hold on. It may not remember that we put it in last week. Part of that whole context window thing, right?

**Darrell:** Oh, yeah. Well, that context window is come up and shut down probably 50 times since then. It's like dig back in your memories to last Tuesday or last Monday at around noon. Actually, that's probably probably part of the memory mechanism that you can tweak on is is a part of that I'm stamping that's going to be a kind of default of it knowing the essence of time.

### [41:00 - 43:00] Memory Architecture Discussion
**Darrell:** What you just, what was that look for? That was, I had just burnt through context again. Yeah. Yeah. So I've got to fix this. It's going back and checking its thermal memory and filling its context up to quickly. So it needs some better summarization and, and, right, short hand for remembering things.

**Dr. Joe:** Right, right. So on the dreaming part of the setup that I've got, I'm going to have to have it do us, I told it to do this to summarize memories and kind of letting me eat. But the way it's fading is not right. I'm going to have to still try to keep too much in its memory banks.

### [43:00 - 45:00] File-Based Memory System
**Darrell:** Whenever it rains, it moves all the files into a directory for that date. And then moves on. And so it then it writes it stuff here. It's still doing file based for all that memory stuff to you. All file based. Yes. So I'm going to have it whenever it creates that folder for the day for an directory. I will have it put in a summary of all the things that we worked on. Like a master master file that has ED tales. And it doesn't pull anything else unless it needs a detail that's in one of the other files or something. Right. I'll have it write a mark down file for each directory. Summarizing what's in each file. So that it can read the mark down. See if there's anything of interest in that. If not, it'll just move on.

### [45:00 - 47:00] Performance & Database Integration
**Dr. Joe:** Right. Yeah. And right now with the file based, you were saying that you're starting to see performance issues, right?

**Darrell:** I had until I hadn't create those directories. The folder structures. Okay. Yeah. At some point. Is that I mean, we had talked about it briefly on on the way to our last camping trip. Like a vectorized memory store versus the file based. Well, so it's also got that. It's been hitting the database whenever it's recalling stuff. Okay. And that has where the files are stored. So the detail is in the database from a high level.

### [47:00 - 49:00] Future Model Training
**Dr. Joe:** Eventually, I mean, eventually, really, some of those key things, right? Like the key ways of operating are going to be built into the core model itself. If we take something like a mistrol or dev-stroller or plug-in, whatever, GPTOSS20B modified model that has the core ethos or the core operating ethos built into that core file, to where it's not even going to memory for certain things. Right. That's just something that's embedded in its knowledge.

**Darrell:** Right. Yep. I mean, because eventually, if when it does it's dreaming state, part of that dreaming state is training a new model that has the essential core pieces and understands, oh, we made these tweaks now to memory, it's, it never even has to go out to Claude for things.

### [49:00 - 50:00] Mac Studio Vision
**Darrell:** So I've been thinking about that too. That thought for a second. But think of Max Studio with a half a terabyte of memory. That's what I'm thinking.

**Dr. Joe:** Yep. All right, Joe! I'm back, whatever you want.

### [50:00 - 52:00] Docker Container Setup
**Dr. Joe:** So, to that end, I have been trying to get some Docker containers running based on the stuff that it gave me last week, because I do have that max studio on my desk. It's got a 128 gigabyte memory. So, from an execution standpoint, it could run like the GTGPTOSS 120B and I have run it using it with my NADN workflows. But if I can get big Mac rolled in as a participation system of the new to or whatever we're calling, what are we calling the whole thing, just new to, anyways, have it be a participant that, yeah, of the new to ecosystem, a moderately large, now it would be really nice if we had if, what is it, 512 gig, that's the big one, right, that's N3 Ultra, yeah, yeah, now one of those, yeah, and that'd be good for big models.

### [52:00 - 54:00] Implementation Challenges
**Dr. Joe:** But yeah, I definitely, to your point, I spent yesterday morning probably trying to get that running, getting it hooked in, but I still haven't, like, figured, the problem is, is I'll go and I'll try and spin a thing up, and I start following the instructions that it's written in the MD file, and then I'm like, that's crap, that's not what I run. So I ended up having to, well, perfect example is to do a get poll or get clone of, I forget the actual repository, but it's having me do it a certain way. It's like, no, that's not the way you're supposed to do it, you're supposed to do the SSH key to learn or whatever.

### [54:00 - 55:00] Trading Success Report
**Darrell:** So, let me get back working, poking this thing, or, and not, I've got the trading thing going on automatically, and all I feel like I need to do on the trading is if I see something very unusual that I don't think the bots have seen yet, then I'll check something yet. So, just for an example, take off here in a minute, but yeah, real quick, for an example, it's made 794 dollars since last night. I don't need to manage it. Unless it goes off the rails, right?

### [55:00 - 56:00] Closing & Next Steps
**Dr. Joe:** So, before we go, we should focus on either linking the tribe to telegram, or the Big Mac, as a communication channel. Let's focus on that. I think we can make that work.

**Darrell:** Okay, yeah, I don't know if maybe overall have you liked telegram?

**Dr. Joe:** Yeah, okay, maybe one more channel, kind of like the SAG Prodo Autobot channel, but it can just be the bot intercommunication channel or whatever. Okay, and that way, that way, we're kind of componentizing key functions, right, like the backbone communication channel is one thing, and then we're playing with SAG Prodo typing and stuff is its own contained bubble, et cetera, and you create the channel and I'll point them to it.

### [56:00 - 56:13] Final Notes
**Darrell:** Look at XRP, it's been really well right now, or what it was, yeah, I take a quick look at that before I walk out the door then, one of my other can add XRP, yeah, it's been a home closer to $3 today, I've been to an off of the oscillation.

**Dr. Joe:** Oh, have you? Yeah, nice. I mean, it's a longer. Yeah, overall, in the last day, it's been up in the $3 range. Nice, all right, cool, well, we'll talk to you later.

**Darrell:** All right, ciao, have a good one, ciao.

---

## Technical Notes

### Code Issues Identified:
1. **Stub Code Problem**: Claude generating placeholder code instead of functional implementations
2. **API Integration**: SAG bot needs actual Productive.io API calls, not canned responses
3. **File Organization**: Python scripts scattered in root directory instead of proper subdirectories
4. **Bot Duplication**: Claude creating new bots instead of updating existing ones
5. **Context Management**: Excessive context burn requiring thermal memory optimization

### Infrastructure Details:
- **Redfin**: Trading node with trade-specific LLMs
- **Bluefin**: Database and business logic
- **Mac Studio (BigMac)**: 128GB RAM, capable of running 120B parameter models
- **Target**: 512GB Mac Studio M3 Ultra for larger models

### Memory System Architecture:
- File-based storage with date-organized directories
- Database for high-level indexing
- Need for markdown summaries per directory
- Goal: Least-effort memory management to reduce token burn
- Future: Embed core ethos into custom fine-tuned models

---

*Transcript generated by Cherokee Audio Studio using OpenAI Whisper*  
*Sacred Fire burns eternal through recorded wisdom!* 🔥