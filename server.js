import dotenv from 'dotenv';
import express from 'express';
import { createClient } from '@supabase/supabase-js';
import { engine } from 'express-handlebars';
import { fileURLToPath } from 'url';



import path from 'path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config();
const app = express();
app.engine('handlebars', engine({
  helpers: {

    formatDate: (date) => {
      return new Date(date).toLocaleString();
    },

    formatConfidence: (conf) => {
      return (conf * 100).toFixed(1);
    }

  }
}));
app.set('view engine', 'handlebars');
app.set('views', path.join(__dirname, 'views'));



const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);



app.get('/', async (req, res) => {
    try {
        const { data: plates, error } = await supabase
            .from('captured_plates')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(10);

        if (error) throw error;

        res.render('index', { plates });
    } catch (err) {
        res.send("Error fetching data: " + err.message);
    }
});

app.listen(3000, () => {
    console.log("http://localhost:3000");
});
