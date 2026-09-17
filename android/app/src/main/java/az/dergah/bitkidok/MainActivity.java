package az.dergah.bitkidok;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.provider.MediaStore;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.tensorflow.lite.Interpreter;
import java.io.InputStream;
import java.io.FileInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int PHOTO = 1;
    private static final int CAMERA = 2;
    private static final String[] LABELS = {
        "money_plant_bacterial_wilt_disease", "money_plant_healthy",
        "money_plant_manganese_toxicity", "snake_plant_anthracnose",
        "snake_plant_healthy", "snake_plant_leaf_withering",
        "spider_plant_fungal_leaf_spot", "spider_plant_healthy",
        "spider_plant_leaf_tip_necrosis"
    };
    private TextView result;
    private ImageView preview;
    private LinearLayout panel;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(32, 35, 32, 25);
        panel.setBackgroundColor(Color.rgb(246, 250, 246));
        TextView title = new TextView(this);
        title.setText("BitkiDok");
        title.setTextSize(30);
        title.setTypeface(null, Typeface.BOLD);
        title.setTextColor(Color.rgb(28, 94, 51));
        panel.addView(title);
        TextView note = new TextView(this);
        note.setText("Offline foto analizi • ilkin sınaq\n10 ev bitkisi üçün növ təxmini. Real fotolarda dəqiqlik ayrıca yoxlanmalıdır; başqa bitkilərdə nəticə səhv ola bilər.");
        note.setTextSize(16);
        note.setPadding(0, 14, 0, 20);
        panel.addView(note);
        Button choose = new Button(this);
        choose.setText("Şəkil seç");
        choose.setOnClickListener(v -> { Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT); pick.setType("image/*"); pick.addCategory(Intent.CATEGORY_OPENABLE); startActivityForResult(pick, PHOTO); });
        panel.addView(choose);
        Button camera = new Button(this);
        camera.setText("Kamera ilə çək");
        camera.setOnClickListener(v -> {
            Intent capture = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            if (capture.resolveActivity(getPackageManager()) != null) startActivityForResult(capture, CAMERA);
            else result.setText("Kamera tətbiqi tapılmadı.");
        });
        panel.addView(camera);
        preview = new ImageView(this);
        preview.setAdjustViewBounds(true);
        preview.setMaxHeight(540);
        panel.addView(preview);
        result = new TextView(this);
        result.setText("Foto seç və ya çək. Şəkil serverə göndərilmir.");
        result.setTextSize(17);
        result.setTextColor(Color.rgb(28, 59, 39));
        result.setPadding(0, 24, 0, 0);
        panel.addView(result);
        android.widget.ScrollView scroll = new android.widget.ScrollView(this);
        scroll.addView(panel);
        setContentView(scroll);
    }

    @Override protected void onActivityResult(int requestCode, int responseCode, Intent data) {
        super.onActivityResult(requestCode, responseCode, data);
        if (responseCode != RESULT_OK || data == null) return;
        try {
            Bitmap photo;
            if (requestCode == PHOTO) {
                try (InputStream stream = getContentResolver().openInputStream(data.getData())) {
                    photo = BitmapFactory.decodeStream(stream);
                }
            } else if (requestCode == CAMERA) {
                photo = (Bitmap) data.getExtras().get("data");
            } else return;
            if (photo == null) throw new IllegalArgumentException("Şəkil açıla bilmədi.");
            preview.setImageBitmap(photo);
            result.setText("Təhlil edilir...");
            final Bitmap input = Bitmap.createScaledBitmap(photo, 224, 224, true);
            new Thread(() -> {
                try {
                    String answer = analyzeSpecies(input);
                    runOnUiThread(() -> result.setText(answer));
                } catch (Exception e) {
                    runOnUiThread(() -> result.setText("Növ modeli açıla bilmədi. Son APK build-ini yoxla."));
                }
            }).start();
        } catch (Exception ex) {
            result.setText("Şəkil oxunmadı. Başqa şəkil seç.");
        }
    }


    private String analyzeSpecies(Bitmap bitmap) throws Exception {
        File model = new File(getCacheDir(), "species.tflite");
        if (!model.exists()) {
            try (InputStream src = getAssets().open("species.tflite");
                 FileOutputStream dst = new FileOutputStream(model)) {
                byte[] block = new byte[16384];
                int n;
                while ((n = src.read(block)) != -1) dst.write(block, 0, n);
            }
        }
        org.json.JSONArray labels;
        try (InputStream src = getAssets().open("species-labels.json");
             java.util.Scanner scanner = new java.util.Scanner(src, "UTF-8")) {
            labels = new org.json.JSONArray(scanner.useDelimiter("\\A").next());
        }
        try (FileInputStream src = new FileInputStream(model);
             FileChannel channel = src.getChannel();
             Interpreter interpreter = new Interpreter(channel.map(FileChannel.MapMode.READ_ONLY, 0, channel.size()))) {
            ByteBuffer pixels = ByteBuffer.allocateDirect(224 * 224 * 3 * 4).order(ByteOrder.nativeOrder());
            int[] colors = new int[224 * 224];
            bitmap.getPixels(colors, 0, 224, 0, 0, 224, 224);
            for (int color : colors) {
                pixels.putFloat(Color.red(color));
                pixels.putFloat(Color.green(color));
                pixels.putFloat(Color.blue(color));
            }
            pixels.rewind();
            float[][] scores = new float[1][labels.length()];
            interpreter.run(pixels, scores);
            int best = 0;
            for (int i = 1; i < labels.length(); i++) {
                if (scores[0][i] > scores[0][best]) best = i;
            }
            float confidence = scores[0][best];
            if (!Float.isFinite(confidence)) throw new IllegalStateException("Invalid model output");
            String latin = labels.getString(best).replace('_', ' ');
            if (confidence < 0.45f) {
                return "Bitki növünü etibarlı müəyyən edə bilmədim. Daha aydın şəkil çək və ya bitkinin adını əl ilə seç.\\n\\nTəklif edilən növ: " + latin + " (model göstəricisi " + String.format(Locale.US, "%.0f%%", confidence * 100) + ").";
            }
            return "Mümkün bitki növü: " + latin
                + "\\nModel göstəricisi: " + String.format(Locale.US, "%.0f%%", confidence * 100)
                + "\\n\\nBu göstərici düzgün tanınma ehtimalı deyil. Model yalnız 10 növ arasında seçim edir və naməlum bitkini də bunlardan birinə aid edə bilər. Xəstəlik nəticəsi bu ekranda verilməyəcək; ayrıca təsdiq tələb edir.";
        }
    }

    private String analyze(Bitmap bitmap) throws Exception {
        File model = new File(getCacheDir(), "model.tflite");
        if (!model.exists()) {
            try (InputStream src = getAssets().open("model.tflite"); FileOutputStream dst = new FileOutputStream(model)) {
                byte[] block = new byte[16384];
                int n;
                while ((n = src.read(block)) != -1) dst.write(block, 0, n);
            }
        }
        try (FileInputStream src = new FileInputStream(model); FileChannel channel = src.getChannel();
             Interpreter interpreter = new Interpreter(channel.map(FileChannel.MapMode.READ_ONLY, 0, channel.size()))) {
            ByteBuffer bytes = ByteBuffer.allocateDirect(1 * 224 * 224 * 3 * 4).order(ByteOrder.nativeOrder());
            int[] pixels = new int[224 * 224];
            bitmap.getPixels(pixels, 0, 224, 0, 0, 224, 224);
            for (int color : pixels) {
                bytes.putFloat(Color.red(color));
                bytes.putFloat(Color.green(color));
                bytes.putFloat(Color.blue(color));
            }
            bytes.rewind();
            float[][] scores = new float[1][LABELS.length];
            interpreter.run(bytes, scores);
            int best = 0;
            for (int i = 1; i < LABELS.length; i++) if (scores[0][i] > scores[0][best]) best = i;
            String plant = best < 3 ? "Pothos / money plant" : best < 6 ? "Sansevieria / snake plant" : "Spider plant";
            String condition;
            switch (best) {
                case 0: condition = "Bakterial solma əlaməti"; break;
                case 1: case 4: case 7: condition = "Sağlam görünüş sinfi"; break;
                case 2: condition = "Manqan artıqlığına bənzər əlamət"; break;
                case 3: condition = "Antraknoza bənzər ləkə"; break;
                case 5: condition = "Yarpaq solması"; break;
                case 6: condition = "Göbələk yarpaq ləkəsinə bənzər əlamət"; break;
                default: condition = "Yarpaq ucunda quruma";
            }
            return "Mümkün bitki: " + plant + "\nMümkün vəziyyət: " + condition
                + "\nModel göstəricisi: " + String.format(Locale.US, "%.0f%%", scores[0][best] * 100)
                + "\n\nBu göstərici diaqnozun dəqiqliyi deyil. Digər bitkilər və naməlum problemlər üçün model yanlış nəticə verə bilər. Kimyəvi müalicəyə başlamazdan əvvəl bitki növünü və səbəbi ayrıca yoxla.";
        }
    }
}
