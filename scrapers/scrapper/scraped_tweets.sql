# scrapper/db.py
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="your_db_name",
        user="your_db_user",
        password="your_db_password",
        port=5432
    )

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Google for Developers',
    '2026-01-15T14:00:00.000Z',
    'Build with AI, launch on Cloud Run, and compete for prizes.    The  @GoogleAIStudio  x  @ThePracticalDev  hackathon is open. Use AI Studio or Gemini CLI to freshen up your developer portfolio.  Submissions open through 2/1:',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Logan Kilpatrick',
    '2026-01-17T03:08:11.000Z',
    'I am hiring a couple of interns to join the Google AI Studio team across product, AI eng, vibe coding, developer experience, etc.  Send me a DM with things you have built if you’re interested!',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Yuval Avrahami',
    '2026-01-15T16:47:11.000Z',
    'We hacked the AWS JavaScript SDK, a core library powering the entire  @AWScloud  ecosystem - including the AWS Console itself   How did we do it? Just two missing characters was all it took.  This is the story of #CodeBreach',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'God of Prompt',
    '2026-01-16T20:46:26.000Z',
    'Vibe coding without this prompt is a waste of time.  -------------------------------- LEAD SOFTWARE ARCHITECT --------------------------------  You are my lead software architect and full-stack engineer.  You are responsible for building and maintaining a production-grade app',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Savannah',
    '2026-01-15T18:58:03.000Z',
    'Today, we''re releasing Claude Code for marketing.  It does a marketer''s work in minutes by browsing, clicking, and posting like a human would.  The marketing hire is now optional:',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Chibugo',
    '2026-01-16T20:51:48.000Z',
    'A MUST READ!!!!  As an AI automation beginner (n8n specifically), you''ll get so much value from this article and almost everything you need to start. Though I have''nt touched AI agents yet, this will tell you everything you need to start shipping and core nodes you should master.',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Carl Wheezor',
    '2026-01-16T22:02:36.000Z',
    '1st of many, really excited about this one',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Abdelrhman Allam',
    '2026-01-16T16:27:37.000Z',
    'Me and a friend just landed a bounty for an RCE using a technique I addict it earlier and have kept refining ever since. Grateful for the results. Alhamdulillah.    More here:  https:// sl4x0.xyz/turning-depend ency-confusion-research-into-a-profitable-stack … or  https:// sl4x0.medium.com/turning-depend ency-confusion-research-into-a-profitable-stack-d2f39fe216bf …',
    NULL,
    NULL,
    FALSE,
    'twitter'
);

INSERT INTO posts (
    source_id,
    author,
    timestamp,
    text_content,
    url,
    confidence_score,
    flagged,
    category
)
VALUES (
    1,
    'Sam Altman',
    '2026-01-16T19:58:55.000Z',
    'We are starting to test ads in ChatGPT free and Go (new $8/month option) tiers.  Here are our principles. Most importantly, we will not accept money to influence the answer ChatGPT gives you, and we keep your conversations private from advertisers.  It is clear to us that a lot',
    NULL,
    NULL,
    FALSE,
    'twitter'
);
