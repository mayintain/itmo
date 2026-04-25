package back;

import java.util.*;

public class ResultsBean {
    private static final ResultsBean INSTANCE = new ResultsBean();

    private final List<HitBean> results =
            Collections.synchronizedList(new ArrayList<>());

    private ResultsBean() {}

    public static ResultsBean getInstance() { 
        return INSTANCE; 
    }

    public void add(HitBean hit) {
         results.add(hit); 
    }

    public List<HitBean> getAll() {
        synchronized (results) {
            return new ArrayList<>(results);
        }
    }

    public void clear() {
        results.clear();
    }

    public int size() {
        return results.size();
    }
}