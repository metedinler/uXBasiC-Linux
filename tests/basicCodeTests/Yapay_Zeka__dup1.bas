MAIN
    PRINT "=== uXBasic ile Basit Yapay Sinir Agi (Neural Network) ==="
    PRINT "Hedef: XOR problemi icin 2-2-1 feedforward sinir agi"
    PRINT "Egitim: Basit backpropagation ile 10000 epoch"
    PRINT ""

    RANDOMIZE TIMER("ms")

    ' =============================================
    ' 1. Ag Yapisi Tanimlari (DIM ile katmanlar)
    ' =============================================
    DIM input(1) AS F64                  ' 2 giris (0..1)
    DIM hidden(1) AS F64                 ' 2 gizli noron
    DIM output(0) AS F64                 ' 1 cikis

    ' Agirliklar ve bias'lar (1D array'ler ile matris simule edildi)
    DIM w_input_hidden(3) AS F64         ' 2x2 = 4 agirlik (0-1: row0, 2-3: row1)
    DIM b_hidden(1) AS F64               ' 2 gizli bias
    DIM w_hidden_output(1) AS F64        ' 2x1 = 2 agirlik
    DIM b_output(0) AS F64               ' 1 cikis bias

    ' Ogrenme parametreleri
    DIM learningRate AS F64 = 0.5
    DIM epochs AS LONG = 10000

    ' =============================================
    ' 2. Agirliklari Rastgele Baslat
    ' =============================================
    CALL InitWeights(w_input_hidden(), b_hidden(), w_hidden_output(), b_output())

    ' =============================================
    ' 3. Egitim Verisi (XOR truth table)
    ' =============================================
    ' Girisler ve beklenen cikislar (4 ornek)
    DIM train_input(3, 1) AS F64         ' 4 satir x 2 sutun
    DIM train_output(3) AS F64           ' 4 satir x 1 sutun

    train_input(0, 0) = 0 : train_input(0, 1) = 0 : train_output(0) = 0
    train_input(1, 0) = 0 : train_input(1, 1) = 1 : train_output(1) = 1
    train_input(2, 0) = 1 : train_input(2, 1) = 0 : train_output(2) = 1
    train_input(3, 0) = 1 : train_input(3, 1) = 1 : train_output(3) = 0

    ' =============================================
    ' 4. Egitim Dongusu
    ' =============================================
    PRINT "Egitim basliyor... (", epochs, " epoch)"
    DIM epoch AS LONG
    FOR epoch = 1 TO epochs
        DIM totalError AS F64 = 0

        DIM sample AS LONG
        FOR sample = 0 TO 3
            ' Girisleri kopyala
            input(0) = train_input(sample, 0)
            input(1) = train_input(sample, 1)

            ' ========================
            ' Forward Pass
            ' ========================
            CALL ForwardPass(input(), hidden(), output(), _
                             w_input_hidden(), b_hidden(), _
                             w_hidden_output(), b_output())

            ' Hata hesapla
            DIM target AS F64 = train_output(sample)
            DIM err AS F64 = target - output(0)
            totalError = totalError + err * err

            ' ========================
            ' Backpropagation (Basit gradient descent)
            ' ========================
            CALL Backprop(input(), hidden(), output(), target, _
                          w_input_hidden(), b_hidden(), _
                          w_hidden_output(), b_output(), _
                          learningRate)
        NEXT sample

        ' Her 2000 epoch'ta ilerleme raporu
        IF epoch MOD 2000 = 0 THEN
            PRINT "Epoch ", epoch, " | Ortalama Hata: ", totalError / 4
        END IF
    NEXT epoch

    PRINT ""
    PRINT "Egitim tamamlandi!"
    PRINT ""

    ' =============================================
    ' 5. Test - Tum XOR kombinasyonlari
    ' =============================================
    PRINT "Test Sonuclari (XOR):"
    DIM i AS LONG, j AS LONG
    FOR i = 0 TO 1
        FOR j = 0 TO 1
            input(0) = i
            input(1) = j

            CALL ForwardPass(input(), hidden(), output(), _
                             w_input_hidden(), b_hidden(), _
                             w_hidden_output(), b_output())

            PRINT i, " XOR ", j, " = ", output(0), "  (beklenen: ", i XOR j, ")"
        NEXT j
    NEXT i

    PRINT ""
    PRINT "uXBasic ile yapay sinir agi basariyla calisti. (Sigmoid aktivasyon + backprop)"
END MAIN

' =============================================
' FONKSIYONLAR
' =============================================

' Sigmoid aktivasyon fonksiyonu
FUNCTION Sigmoid(x AS F64) AS F64
    Sigmoid = 1 / (1 + EXP(-x))
END FUNCTION

' Sigmoid turevi (backprop icin)
FUNCTION SigmoidDerivative(y AS F64) AS F64
    SigmoidDerivative = y * (1 - y)
END FUNCTION

' Agirliklari rastgele baslat (0.0 - 1.0 arasi)
SUB InitWeights(w_ih() AS F64, b_h() AS F64, w_ho() AS F64, b_o() AS F64)
    DIM k AS LONG
    FOR k = 0 TO 3
        w_ih(k) = RND(1) - 0.5
    NEXT k
    FOR k = 0 TO 1
        b_h(k) = RND(1) - 0.5
        w_ho(k) = RND(1) - 0.5
    NEXT k
    b_o(0) = RND(1) - 0.5
END SUB

' Forward Pass (2-2-1 ag)
SUB ForwardPass(inp() AS F64, hid() AS F64, out() AS F64, _
                w_ih() AS F64, b_h() AS F64, _
                w_ho() AS F64, b_o() AS F64)
    ' Gizli katman
    hid(0) = Sigmoid( inp(0)*w_ih(0) + inp(1)*w_ih(1) + b_h(0) )
    hid(1) = Sigmoid( inp(0)*w_ih(2) + inp(1)*w_ih(3) + b_h(1) )

    ' Cikis katmani
    out(0) = Sigmoid( hid(0)*w_ho(0) + hid(1)*w_ho(1) + b_o(0) )
END SUB

' Basit Backpropagation (tek ornek icin)
SUB Backprop(inp() AS F64, hid() AS F64, out() AS F64, target AS F64, _
             w_ih() AS F64, b_h() AS F64, _
             w_ho() AS F64, b_o() AS F64, _
             lr AS F64)
    DIM output_error AS F64 = target - out(0)
    DIM output_delta AS F64 = output_error * SigmoidDerivative(out(0))

    ' Gizli katman delta'ları
    DIM hidden_delta(1) AS F64
    hidden_delta(0) = output_delta * w_ho(0) * SigmoidDerivative(hid(0))
    hidden_delta(1) = output_delta * w_ho(1) * SigmoidDerivative(hid(1))

    ' Agirlik guncellemeleri
    ' Cikis katmani agirliklari
    w_ho(0) = w_ho(0) + lr * output_delta * hid(0)
    w_ho(1) = w_ho(1) + lr * output_delta * hid(1)
    b_o(0) = b_o(0) + lr * output_delta

    ' Gizli katman agirliklari
    w_ih(0) = w_ih(0) + lr * hidden_delta(0) * inp(0)
    w_ih(1) = w_ih(1) + lr * hidden_delta(0) * inp(1)
    w_ih(2) = w_ih(2) + lr * hidden_delta(1) * inp(0)
    w_ih(3) = w_ih(3) + lr * hidden_delta(1) * inp(1)

    b_h(0) = b_h(0) + lr * hidden_delta(0)
    b_h(1) = b_h(1) + lr * hidden_delta(1)
END SUB